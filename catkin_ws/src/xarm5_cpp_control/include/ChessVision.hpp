#ifndef CHESS_VISION_HPP
#define CHESS_VISION_HPP

#include <ros/ros.h>
#include <image_transport/image_transport.h>
#include <cv_bridge/cv_bridge.h>
#include <opencv2/opencv.hpp>
#include <vector>
#include <string>
#include <map>
#include <cmath>
#include <random>

// Визначення шахової фігури
enum class PieceType { WHITE, BLACK, EMPTY, UNKNOWN };

/**
 * @brief Клас для обробки зображень з камери та визначення стану шахової дошки.
 */
class ChessVision {
private:
    ros::NodeHandle nh_;
    image_transport::ImageTransport it_;
    image_transport::Subscriber image_sub_;
    cv::Mat current_image_;
    bool new_image_received_ = false;

    // --- ДИНАМІЧНІ ПАРАМЕТРИ ROI ---
    cv::Rect board_roi_;
    int cell_size_px_ = 0;
    bool calibration_successful_ = false;
    bool manual_calibration_ = false;

    // Ручна калібрування (координати з вашого launch-файлу)
    const double MANUAL_A1_X = -0.29931;
    const double MANUAL_A1_Y = -0.21875;
    const double MANUAL_STEP = 0.0625;

    // Генератор випадкових чисел
    std::random_device rd_;
    std::mt19937 gen_;

    // Параметри для налаштування розпізнавання
    double white_piece_on_white_cell_min_;
    double black_piece_on_white_cell_max_;
    double white_piece_on_black_cell_min_;
    double black_piece_on_black_cell_max_;

    /**
     * @brief Покращена класифікація клітинки з урахуванням реальних значень з камери
     */
    PieceType classifyCell(const cv::Mat& cell_image, int file, int rank) const {
        if (cell_image.empty() || cell_image.rows < 10 || cell_image.cols < 10) {
            ROS_WARN("Cell (%d,%d) - Empty or too small image", file, rank);
            return PieceType::UNKNOWN;
        }

        // Збільшимо область аналізу
        int margin_h = cell_image.rows / 6;
        int margin_w = cell_image.cols / 6;
        cv::Rect center_roi(margin_w, margin_h, cell_image.cols - 2*margin_w, cell_image.rows - 2*margin_h);

        if (center_roi.width <= 0 || center_roi.height <= 0) {
            return PieceType::UNKNOWN;
        }

        cv::Mat center_cell = cell_image(center_roi);

        // Збережемо зображення для дебагу
        std::string debug_filename = "/tmp/cell_" + std::to_string(file) + "_" + std::to_string(rank) + ".jpg";
        cv::imwrite(debug_filename, center_cell);

        // Конвертуємо в HSV для кращого аналізу кольору
        cv::Mat hsv_image;
        cv::cvtColor(center_cell, hsv_image, cv::COLOR_BGR2HSV);

        // Розділяємо канали
        std::vector<cv::Mat> hsv_channels;
        cv::split(hsv_image, hsv_channels);

        cv::Mat v_channel = hsv_channels[2]; // Яскравість

        // Обчислюємо статистику
        cv::Scalar mean_bgr = cv::mean(center_cell);
        cv::Scalar mean_hsv = cv::mean(hsv_image);
        cv::Scalar std_dev_bgr;
        cv::meanStdDev(center_cell, mean_bgr, std_dev_bgr);

        double intensity = mean_bgr[2]; // Використовуємо червоний канал (найчутливіший)
        double saturation = mean_hsv[1];
        double value = mean_hsv[2];
        double std_dev = std_dev_bgr[2]; // Стандартне відхилення для виявлення текстур

        // ПОЛІПШЕНИЙ аналіз текстури
        cv::Mat gray;
        cv::cvtColor(center_cell, gray, cv::COLOR_BGR2GRAY);
        cv::Mat laplacian;
        cv::Laplacian(gray, laplacian, CV_64F);
        cv::Scalar mean_lap, std_lap;
        cv::meanStdDev(laplacian, mean_lap, std_lap);
        double texture = std_lap[0]; // Варіація яскравості

        bool is_white_cell = ((file + rank) % 2 == 0);

        // ДЕТАЛЬНЕ ЛОГУВАННЯ
        ROS_INFO("Cell (%d,%d) - Int: %.1f, Sat: %.1f, Val: %.1f, StdDev: %.2f, Texture: %.2f, WhiteCell: %d",
                  file, rank, intensity, saturation, value, std_dev, texture, is_white_cell);

        // ОНОВЛЕНА ЛОГІКА КЛАСИФІКАЦІЇ з реальними значеннями
        if (is_white_cell) {
            // БІЛА клітинка
            if (intensity < 120.0 && texture > 8.0) {  // Темно + текстура = чорна фігура
                ROS_INFO("  -> BLACK piece on white cell");
                return PieceType::BLACK;
            } else if (intensity > 160.0 && texture > 12.0) {  // Дуже яскраво + текстура = біла фігура
                ROS_INFO("  -> WHITE piece on white cell");
                return PieceType::WHITE;
            } else if (intensity > 170.0 && texture < 5.0) {  // Дуже яскраво + мало текстури = порожня
                ROS_INFO("  -> EMPTY white cell");
                return PieceType::EMPTY;
            } else {
                ROS_INFO("  -> UNKNOWN on white cell");
                return PieceType::UNKNOWN;
            }
        } else {
            // ЧОРНА клітинка
            if (intensity > 130.0 && texture > 10.0) {  // Яскраво на чорній + текстура
                ROS_INFO("  -> WHITE piece on black cell");
                return PieceType::WHITE;
            } else if (intensity < 100.0 && texture > 6.0) {  // Дуже темно + текстура
                ROS_INFO("  -> BLACK piece on black cell");
                return PieceType::BLACK;
            } else if (intensity < 80.0 && texture < 4.0) {  // Дуже темно + мало текстури = порожня
                ROS_INFO("  -> EMPTY black cell");
                return PieceType::EMPTY;
            } else {
                ROS_INFO("  -> UNKNOWN on black cell");
                return PieceType::UNKNOWN;
            }
        }
    }

    /**
     * @brief Ручна калібрування дошки за відомими координатами
     */
    bool manualCalibrateBoard(const cv::Mat& input_image) {
        ROS_INFO("Using manual calibration based on known board coordinates");

        // Емпіричні значення - налаштування під вашу камеру
        const double PIXELS_PER_METER = 350.0;

        int center_x = input_image.cols / 2;
        int center_y = input_image.rows / 2;

        // Розраховуємо розміри дошки в пікселях
        int board_width_px = static_cast<int>(8 * MANUAL_STEP * PIXELS_PER_METER);
        int board_height_px = static_cast<int>(8 * MANUAL_STEP * PIXELS_PER_METER);
        cell_size_px_ = static_cast<int>(MANUAL_STEP * PIXELS_PER_METER);

        // Центруємо дошку на зображенні
        int roi_x = center_x - board_width_px / 2;
        int roi_y = center_y - board_height_px / 2 - 50; // Зсув вгору для компенсації

        // Переконуємося, що ROI в межах зображення
        roi_x = std::max(0, roi_x);
        roi_y = std::max(0, roi_y);
        int roi_width = std::min(input_image.cols - roi_x, board_width_px);
        int roi_height = std::min(input_image.rows - roi_y, board_height_px);

        if (roi_width > 0 && roi_height > 0) {
            board_roi_ = cv::Rect(roi_x, roi_y, roi_width, roi_height);
            calibration_successful_ = true;
            manual_calibration_ = true;

            ROS_INFO("Manual calibration successful: ROI (%d, %d, %d, %d), Cell Size: %d px",
                     roi_x, roi_y, roi_width, roi_height, cell_size_px_);

            // Збережемо зображення для налагодження
            cv::Mat debug_image = input_image.clone();
            cv::rectangle(debug_image, board_roi_, cv::Scalar(0, 255, 0), 2);

            // Намалюємо сітку клітинок
            for (int i = 0; i <= 8; i++) {
                cv::line(debug_image,
                        cv::Point(roi_x + i * cell_size_px_, roi_y),
                        cv::Point(roi_x + i * cell_size_px_, roi_y + roi_height),
                        cv::Scalar(255, 0, 0), 1);
                cv::line(debug_image,
                        cv::Point(roi_x, roi_y + i * cell_size_px_),
                        cv::Point(roi_x + roi_width, roi_y + i * cell_size_px_),
                        cv::Scalar(255, 0, 0), 1);
            }

            cv::imwrite("/tmp/chessboard_manual_calibration.jpg", debug_image);
            return true;
        }

        ROS_WARN("Manual calibration failed - ROI out of bounds");
        return false;
    }

    /**
     * @brief Автоматично знаходить кути шахової дошки
     */
    bool autoCalibrateBoard(const cv::Mat& input_image) {
        if (input_image.empty()) {
            ROS_WARN("Calibration failed: Input image is empty.");
            return false;
        }

        cv::Mat gray_image;
        cv::cvtColor(input_image, gray_image, cv::COLOR_BGR2GRAY);

        // Покращена обробка зображення
        cv::Mat blurred, binary;
        cv::GaussianBlur(gray_image, blurred, cv::Size(5, 5), 0);
        cv::adaptiveThreshold(blurred, binary, 255,
                             cv::ADAPTIVE_THRESH_GAUSSIAN_C, cv::THRESH_BINARY, 11, 2);

        // Спробуємо різні розміри шаблону
        std::vector<cv::Size> pattern_sizes = {
            cv::Size(7, 7),  // Стандартний для шахів
            cv::Size(6, 6),
            cv::Size(8, 8)
        };

        std::vector<cv::Point2f> corners;
        bool found = false;

        for (const auto& pattern_size : pattern_sizes) {
            corners.clear();
            found = cv::findChessboardCorners(binary, pattern_size, corners,
                       cv::CALIB_CB_ADAPTIVE_THRESH + cv::CALIB_CB_NORMALIZE_IMAGE + cv::CALIB_CB_FAST_CHECK);

            if (found) {
                // Уточнюємо знайдені кути
                cv::cornerSubPix(gray_image, corners, cv::Size(11, 11), cv::Size(-1, -1),
                    cv::TermCriteria(cv::TermCriteria::EPS + cv::TermCriteria::COUNT, 30, 0.1));

                ROS_INFO("Found chessboard with pattern %dx%d", pattern_size.width, pattern_size.height);
                break;
            }
        }

        if (found) {
            cv::Point2f min_point = corners[0];
            cv::Point2f max_point = corners[0];

            for (const auto& p : corners) {
                min_point.x = std::min(min_point.x, p.x);
                min_point.y = std::min(min_point.y, p.y);
                max_point.x = std::max(max_point.x, p.x);
                max_point.y = std::max(max_point.y, p.y);
            }

            int board_width_px = static_cast<int>(max_point.x - min_point.x);
            int board_height_px = static_cast<int>(max_point.y - min_point.y);

            cell_size_px_ = static_cast<int>(std::round(board_width_px / 7.0));

            int offset_x = cell_size_px_ / 2;
            int offset_y = cell_size_px_ / 2;

            int roi_x = static_cast<int>(std::round(min_point.x)) - offset_x;
            int roi_y = static_cast<int>(std::round(min_point.y)) - offset_y;
            int roi_width = board_width_px + cell_size_px_;
            int roi_height = board_height_px + cell_size_px_;

            roi_x = std::max(0, roi_x);
            roi_y = std::max(0, roi_y);
            roi_width = std::min(input_image.cols - roi_x, roi_width);
            roi_height = std::min(input_image.rows - roi_y, roi_height);

            if (roi_width > 0 && roi_height > 0) {
                board_roi_ = cv::Rect(roi_x, roi_y, roi_width, roi_height);
                calibration_successful_ = true;

                // Візуалізація для налагодження
                cv::Mat debug_image = input_image.clone();
                cv::rectangle(debug_image, board_roi_, cv::Scalar(0, 255, 0), 2);
                for (const auto& corner : corners) {
                    cv::circle(debug_image, corner, 3, cv::Scalar(0, 0, 255), -1);
                }
                cv::imwrite("/tmp/chessboard_auto_calibration.jpg", debug_image);

                ROS_INFO("Auto calibration successful: ROI (%d, %d, %d, %d), Cell Size: %d px",
                         roi_x, roi_y, roi_width, roi_height, cell_size_px_);
                return true;
            }
        }

        ROS_WARN("Auto calibration failed - chessboard pattern not found");
        return false;
    }

    /**
     * @brief Callback-функція для отримання нового зображення з камери.
     */
    void imageCallback(const sensor_msgs::ImageConstPtr& msg) {
        try {
            cv_bridge::CvImagePtr cv_ptr;
            cv_ptr = cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::BGR8);
            current_image_ = cv_ptr->image;
            new_image_received_ = true;

            ROS_DEBUG("Received image: %dx%d", current_image_.cols, current_image_.rows);

            if (!calibration_successful_) {
                // Спочатку пробуємо автоматичну калібрування
                if (!autoCalibrateBoard(current_image_)) {
                    // Якщо автоматична не вдалась, використовуємо ручну
                    ROS_WARN("Auto calibration failed, trying manual calibration...");
                    manualCalibrateBoard(current_image_);
                }
            }

        } catch (cv_bridge::Exception& e) {
            ROS_ERROR("cv_bridge exception: %s", e.what());
        } catch (const std::exception& e) {
            ROS_ERROR("Exception in imageCallback: %s", e.what());
        }
    }

public:
    ChessVision(ros::NodeHandle& nh) : nh_(nh), it_(nh), gen_(rd_()) {
        // Завантажуємо параметри
        nh_.param("white_piece_on_white_cell_min", white_piece_on_white_cell_min_, 170.0);
        nh_.param("black_piece_on_white_cell_max", black_piece_on_white_cell_max_, 90.0);
        nh_.param("white_piece_on_black_cell_min", white_piece_on_black_cell_min_, 130.0);
        nh_.param("black_piece_on_black_cell_max", black_piece_on_black_cell_max_, 70.0);

        // Підписка на топік камери
        image_sub_ = it_.subscribe("/overhead_camera/image_raw", 1, &ChessVision::imageCallback, this);

        ROS_INFO("ChessVision initialized with parameters:");
        ROS_INFO("  White piece on white cell min: %.1f", white_piece_on_white_cell_min_);
        ROS_INFO("  Black piece on white cell max: %.1f", black_piece_on_white_cell_max_);
        ROS_INFO("  White piece on black cell min: %.1f", white_piece_on_black_cell_min_);
        ROS_INFO("  Black piece on black cell max: %.1f", black_piece_on_black_cell_max_);
        ROS_INFO("Subscribed to /overhead_camera/image_raw for chess vision.");
    }

    /**
     * @brief Перевіряє, чи було успішно виконано калібрування дошки.
     */
    bool isCalibrated() const {
        return calibration_successful_;
    }

    /**
     * @brief Зчитує поточний стан шахової дошки
     */
    std::vector<std::vector<PieceType>> getCurrentBoardState() {
        std::vector<std::vector<PieceType>> board_state(8, std::vector<PieceType>(8, PieceType::UNKNOWN));

        if (!calibration_successful_ || current_image_.empty() || cell_size_px_ == 0) {
            ROS_WARN("Cannot read board state: Vision not calibrated or image missing.");
            return board_state;
        }

        // 1. Обрізаємо зображення дошки (ROI)
        cv::Mat board_image;
        try {
            board_image = current_image_(board_roi_);
        } catch (const cv::Exception& e) {
            ROS_ERROR("OpenCV error while cropping ROI: %s", e.what());
            return board_state;
        }

        // 2. Аналіз кожної клітинки
        for (int file = 0; file < 8; ++file) {
            for (int rank = 0; rank < 8; ++rank) {
                // Розрахунок ROI для поточної клітинки
                cv::Rect cell_roi(file * cell_size_px_, rank * cell_size_px_, cell_size_px_, cell_size_px_);

                if (cell_roi.x >= 0 && cell_roi.y >= 0 &&
                    cell_roi.x + cell_size_px_ <= board_image.cols &&
                    cell_roi.y + cell_size_px_ <= board_image.rows)
                {
                    cv::Mat cell_image = board_image(cell_roi);
                    board_state[file][rank] = classifyCell(cell_image, file, rank);
                } else {
                    ROS_WARN("Cell ROI out of bounds for (%d, %d)", file, rank);
                }
            }
        }

        return board_state;
    }

    /**
     * @brief Знаходить всі можливі ходи для білих фігур
     */
    std::vector<std::pair<std::string, std::string>> findPossibleWhiteMoves() {
        std::vector<std::pair<std::string, std::string>> possible_moves;
        auto board_state = getCurrentBoardState();

        // Знаходимо всі білі фігури
        std::vector<std::string> white_pieces;
        for (int file = 0; file < 8; ++file) {
            for (int rank = 0; rank < 8; ++rank) {
                if (board_state[file][rank] == PieceType::WHITE) {
                    white_pieces.push_back(indexToSquare(file, rank));
                }
            }
        }

        // Для кожної білої фігури знаходимо всі порожні клітинки
        for (const auto& from_square : white_pieces) {
            for (int file = 0; file < 8; ++file) {
                for (int rank = 0; rank < 8; ++rank) {
                    if (board_state[file][rank] == PieceType::EMPTY) {
                        std::string to_square = indexToSquare(file, rank);
                        possible_moves.push_back({from_square, to_square});
                    }
                }
            }
        }

        ROS_INFO("Found %zu possible moves for white pieces", possible_moves.size());
        return possible_moves;
    }

    /**
     * @brief Вибирає випадковий хід для білих фігур
     */
    std::pair<std::string, std::string> getRandomWhiteMove() {
        // ТИМЧАСОВО: примусово задамо хід для тестування
        ROS_WARN("USING HARDCODED MOVE FOR TESTING");

        // Спрощений підхід - просто перемістимо пішака з a2 на a3
        return {"a2", "a3"};

        /* Закоментуйте оригінальний код поки що
        auto possible_moves = findPossibleWhiteMoves();

        if (possible_moves.empty()) {
            ROS_WARN("No possible moves found for white pieces!");
            return {"", ""};
        }

        std::uniform_int_distribution<> dis(0, possible_moves.size() - 1);
        int random_index = dis(gen_);

        auto move = possible_moves[random_index];
        ROS_INFO("Selected random move: %s to %s", move.first.c_str(), move.second.c_str());

        return move;
        */
    }

    /**
     * @brief Конвертує індекси у шахову клітинку
     */
    std::string indexToSquare(int file, int rank) const {
        if (file < 0 || file > 7 || rank < 0 || rank > 7) {
            return "INVALID";
        }
        return std::string() + static_cast<char>('a' + file) + static_cast<char>('1' + rank);
    }

    /**
     * @brief Зберігає поточне зображення для налагодження
     */
    void saveDebugImage(const std::string& filename) {
        if (!current_image_.empty()) {
            cv::imwrite(filename, current_image_);
            ROS_INFO("Debug image saved: %s", filename.c_str());
        }
    }

    /**
     * @brief Дебаг калібрування - зберігає зображення для аналізу
     */
    void debugCalibration() {
        if (!current_image_.empty()) {
            // Збережемо оригінальне зображення
            cv::imwrite("/tmp/chessboard_original.jpg", current_image_);

            // Збережемо обрізане зображення дошки
            if (calibration_successful_) {
                cv::Mat board_image = current_image_(board_roi_);
                cv::imwrite("/tmp/chessboard_cropped.jpg", board_image);

                // Намалюємо сітку на обрізаному зображенні
                cv::Mat debug_board = board_image.clone();
                for (int i = 0; i <= 8; i++) {
                    cv::line(debug_board,
                            cv::Point(i * cell_size_px_, 0),
                            cv::Point(i * cell_size_px_, debug_board.rows),
                            cv::Scalar(0, 255, 0), 1);
                    cv::line(debug_board,
                            cv::Point(0, i * cell_size_px_),
                            cv::Point(debug_board.cols, i * cell_size_px_),
                            cv::Scalar(0, 255, 0), 1);
                }
                cv::imwrite("/tmp/chessboard_with_grid.jpg", debug_board);
            }

            ROS_INFO("Debug images saved to /tmp/");
        }
    }

    /**
     * @brief Перевіряє роботу камери та зберігає повне зображення
     */
    void debugCameraSetup() {
        if (current_image_.empty()) {
            ROS_WARN("No image received from camera yet");
            return;
        }

        ROS_INFO("=== CAMERA DEBUG INFO ===");
        ROS_INFO("Image size: %dx%d", current_image_.cols, current_image_.rows);
        ROS_INFO("Image channels: %d", current_image_.channels());

        // Збережемо повне зображення
        cv::imwrite("/tmp/full_camera_view.jpg", current_image_);

        // Перевіримо середню яскравість
        cv::Scalar mean = cv::mean(current_image_);
        ROS_INFO("Image mean BGR: [%.1f, %.1f, %.1f]", mean[0], mean[1], mean[2]);

        // Збережемо обрізану дошку
        if (calibration_successful_) {
            cv::Mat board_view = current_image_(board_roi_);
            cv::imwrite("/tmp/board_view.jpg", board_view);

            cv::Scalar board_mean = cv::mean(board_view);
            ROS_INFO("Board mean BGR: [%.1f, %.1f, %.1f]", board_mean[0], board_mean[1], board_mean[2]);
        }

        ROS_INFO("Debug images saved to /tmp/");
    }
};

#endif // CHESS_VISION_HPP