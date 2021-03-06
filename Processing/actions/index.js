const config = require('./../../config.json')
const actionTypes = require('./actionTypes')
const fs = require('fs');
const path = require('path')
const fsX = require('fs-extra');
const chalk = require('chalk');
const moment = require('moment');
const logWriter = require('./../utils/sightingEventHandler')
const axios = require('axios')
const encode = require('./../utils/addChunkToPng')
const processedRecordLog = new logWriter({path: config.PROCESSED_LOGS_PATH})

const workerpool = require('workerpool')
const pool = workerpool.pool()

const hashingWorker = (data, pathin, pathout, encode) => {
    encode(data, pathin, pathout,
        () => {
            fs.unlink(pathin,(err)=>{
                if (err) console.log(err);
            })
        }
    )
}

const convertNameToObj = (meta) => {
    const fileType = `.${meta.split('.')[1]}`
    const parts = meta.split('.')[0].split("_")
    return parts.reduce((obj,i)=>{
        let attr = i.split("=")
        return {
            ...obj,
            [attr[0]]:attr[1]
        }
    }, {fileType, fileName: meta})
}



module.exports = actionHandler = (action) => {
    
    if(action.type === actionTypes.rawStoreFileUpdated){
        const pathComps = action.payload.path.split("/")
        const { CAM, UNIX, fileType, ID, PLATE, fileName } = convertNameToObj(pathComps[pathComps.length-1])
        axios.get('http://192.168.1.100:8000/gps-coords')
            .then(function (response) {
                const { lat, lon, time } = response.data
                const objToWrite = {
                    ID: ID,
                    timeUNIX: UNIX,
                    timeISO: moment.unix(Math.round(UNIX/1000)).toISOString(),
                    timeGPS: time,
                    GPS_COORDS: `${lat}, ${lon}`,
                    CAM,
                    PLATE,
                    PATH: fileName
                }
                processedRecordLog.write(objToWrite)
                console.log(chalk.black.bgYellow('Action Received: ', action.type))
                return response.data
            }).catch(err=>console.log(err))     
            
            /* .then(()=>{
                fsX.move(action.payload.path, path.join(config.BACKUP_LOCATIONS[0], fileName) , {overwrite: true}, (err) => {
                    if (err) console.log("Error Backing up: %s", fileName, err)
                    console.log('Backed up %s', fileName)
                })
            }) */
            
            /* .then(data => {
                encode({
                        direction_of_travel: "west",
                        gps_latitude: data.lat,
                        gps_longitude: data.lon,
                        gps_time_iso: data.time,
                        capture_time_unixms: UNIX,
                    }, action.payload.path, `${config.BACKUP_LOCATIONS[0]}ID=${ID}_CAM=${CAM}_PLATE=${'ERROR'}_UNIX=${UNIX}${fileType}`,
                    CAM==="CAM6"
                    ,
                    () => {
                        fs.unlink(action.payload.path,(err)=>{
                            if (err) console.log(err);
                        })
                    }
                )
            }) */
    }
    /* if(action.type === actionTypes.processedStoreFileUpdated){
        // backup to external and unlink
        const pathComps = action.payload.path.split("/")
        const { CAM, UNIX, fileType, ID, PLATE, fileName } = convertNameToObj(pathComps[pathComps.length-1])
        fsX.move(action.payload.path, path.join(config.BACKUP_LOCATIONS[0], fileName) , {overwrite: true}, (err) => {
            if (err) console.log("Error Backing up: %s", fileName, err)
            console.log('Backed up %s', fileName)
        })
    }
    if(false && action.type === actionTypes.rawStoreFileUpdated){
        const pathComps = action.payload.path.split("/")
        const { CAM, UNIX, fileType, ID, PLATE, fileName } = convertNameToObj(pathComps[pathComps.length-1])
        axios.get('http://192.168.1.100:8000/gps-coords')
            .then(function (response) {
                const { lat, lon, time } = response.data
                const objToWrite = {
                    ID: ID,
                    timeUNIX: UNIX,
                    timeISO: moment.unix(Math.round(UNIX/1000)).toISOString(),
                    timeGPS: time,
                    GPS_COORDS: `${lat}, ${lon}`,
                    CAM,
                    PLATE,
                    PATH: fileName
                }
                processedRecordLog.write(objToWrite)
                return response.data
            }).then(data => {
                const dataToWrite = {
                    direction_of_travel: "west",
                    gps_latitude: data.lat,
                    gps_longitude: data.lon,
                    gps_time_iso: data.time,
                    capture_time_unixms: UNIX,
                }
                const pathin = action.payload.path
                const pathout = `${config.BACKUP_LOCATIONS[0]}ID=${ID}_CAM=${CAM}_PLATE=${'ERROR'}_UNIX=${UNIX}${fileType}`
                pool.exec(hashingWorker, [dataToWrite, pathin, pathout], encode).then(res=>console.log("done")).catch(err=>console.log(err))
            }).catch(err=>console.log(err))     
    }
    if(action.type === actionTypes.processedStoreFileUpdated){
        // backup to external and unlink
        const pathComps = action.payload.path.split("/")
        const { CAM, UNIX, fileType, ID, PLATE, fileName } = convertNameToObj(pathComps[pathComps.length-1])
        fsX.move(action.payload.path, path.join(config.BACKUP_LOCATIONS[0], fileName) , {overwrite: true}, (err) => {
            if (err) console.log("Error Backing up: %s", fileName, err)
            console.log('Backed up %s', fileName)
        })
    } */
}