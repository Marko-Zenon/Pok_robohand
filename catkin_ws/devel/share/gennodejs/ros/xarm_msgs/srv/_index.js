
"use strict";

let GetInt32 = require('./GetInt32.js')
let GetErr = require('./GetErr.js')
let SetString = require('./SetString.js')
let SetLoad = require('./SetLoad.js')
let Move = require('./Move.js')
let GetDigitalIO = require('./GetDigitalIO.js')
let GripperMove = require('./GripperMove.js')
let GripperState = require('./GripperState.js')
let FtIdenLoad = require('./FtIdenLoad.js')
let Call = require('./Call.js')
let MoveAxisAngle = require('./MoveAxisAngle.js')
let GetSetModbusData = require('./GetSetModbusData.js')
let TCPOffset = require('./TCPOffset.js')
let VacuumGripperCtrl = require('./VacuumGripperCtrl.js')
let GetFloat32List = require('./GetFloat32List.js')
let SetInt16 = require('./SetInt16.js')
let SetDigitalIO = require('./SetDigitalIO.js')
let SetFloat32 = require('./SetFloat32.js')
let SetModbusTimeout = require('./SetModbusTimeout.js')
let MoveVelo = require('./MoveVelo.js')
let SetToolModbus = require('./SetToolModbus.js')
let SetControllerAnalogIO = require('./SetControllerAnalogIO.js')
let SetMultipleInts = require('./SetMultipleInts.js')
let GetControllerDigitalIO = require('./GetControllerDigitalIO.js')
let PlayTraj = require('./PlayTraj.js')
let FtCaliLoad = require('./FtCaliLoad.js')
let ConfigToolModbus = require('./ConfigToolModbus.js')
let SetAxis = require('./SetAxis.js')
let MoveVelocity = require('./MoveVelocity.js')
let ClearErr = require('./ClearErr.js')
let GripperConfig = require('./GripperConfig.js')
let GetAnalogIO = require('./GetAnalogIO.js')

module.exports = {
  GetInt32: GetInt32,
  GetErr: GetErr,
  SetString: SetString,
  SetLoad: SetLoad,
  Move: Move,
  GetDigitalIO: GetDigitalIO,
  GripperMove: GripperMove,
  GripperState: GripperState,
  FtIdenLoad: FtIdenLoad,
  Call: Call,
  MoveAxisAngle: MoveAxisAngle,
  GetSetModbusData: GetSetModbusData,
  TCPOffset: TCPOffset,
  VacuumGripperCtrl: VacuumGripperCtrl,
  GetFloat32List: GetFloat32List,
  SetInt16: SetInt16,
  SetDigitalIO: SetDigitalIO,
  SetFloat32: SetFloat32,
  SetModbusTimeout: SetModbusTimeout,
  MoveVelo: MoveVelo,
  SetToolModbus: SetToolModbus,
  SetControllerAnalogIO: SetControllerAnalogIO,
  SetMultipleInts: SetMultipleInts,
  GetControllerDigitalIO: GetControllerDigitalIO,
  PlayTraj: PlayTraj,
  FtCaliLoad: FtCaliLoad,
  ConfigToolModbus: ConfigToolModbus,
  SetAxis: SetAxis,
  MoveVelocity: MoveVelocity,
  ClearErr: ClearErr,
  GripperConfig: GripperConfig,
  GetAnalogIO: GetAnalogIO,
};
