const chokidar = require('chokidar')
const config = require('./../config.json')
const chalk = require('chalk');
const moment = require('moment')
const fs = require('fs-extra')
const path = require('path');

const WATCH_PATH = config.PROCESSED_STORE_PATH
const BACKUP_LOCATIONS = config.BACKUP_LOCATIONS
const BACKUP_BUFFER = config.AUTO_BACKUP_BUFFER
const EVENT_LOGS_PATH = config.EVENT_LOGS_PATH
const PROCESSED_LOGS_PATH = config.PROCESSED_LOGS_PATH

const DELETE_ON_BACKUP = true

console.log(chalk.bgGreen.bold.black("STARTING AUTO BACKUP SCRIPTS ..."))
console.log(chalk.bgGreen.black(`Now watching '${WATCH_PATH}' for Auto Backup to ${BACKUP_LOCATIONS.join(", ")} | Buffer length: ${BACKUP_BUFFER}`))

class fileBackupQueue {
    constructor({bufferLength, watchPath, backupPath}){
        this.bufferLength = bufferLength
        this.watchPath = watchPath
        this.stack = []
        this.backupStack = []
        this.isBackingUp = false
        this.lastBackedUp = null
        this.backupPath = Array.isArray(backupPath)?backupPath:[backupPath]
    }

    initBackup() {
        if (this.stack.length < this.bufferLength) {
            console.log(chalk.bold.yellow('WARNING: BACKUP WAS MANUALLY INITIATED BEFORE THE SET BUFFER LENGTH'))
        }
        // backup to backupPaths
        this.isBackingUp = true
        this.backupStack = [...this.stack]
        this.stack = []
        this.backupFiles().then(()=>{
            this.isBackingUp = false
            this.backupStack = []
            this.lastBackedUp = moment()
        })
    }

    backupFiles() {
        return Promise.all( this.backupStack.map(file => {
            return Promise.all(
                this.backupPath.map(bpath=>fs.copy(path.join(this.watchPath,file), path.join(bpath,file)).catch(err=>console.log(err)))
            ).then(res=>console.log("Backup Complete."))
        }))
        .then(
            res => {
                //backup log files
                return Promise.all(this.backupPath.map(bpath => ([
                    fs.copy(EVENT_LOGS_PATH, path.join(bpath,'events.csv')),
                    fs.copy(PROCESSED_LOGS_PATH, path.join(bpath,'processed.csv'))
                ])))
            }
        ).then(()=>{
            if (DELETE_ON_BACKUP){
                console.log('CLEARING HD BUFFERS')
                return Promise.all(this.backupStack.map(file=>fs.remove(path.join(this.watchPath,file))))
            } else {
                return null
            }
        }).catch(err=>console.log(err))
    }

    add(item) {
        this.stack = [...this.stack, item]
        const message = `${this.isBackingUp?"Is Backing up! ":""}Current buffer at: ${this.stack.length} item ( ${Math.round(100*(this.stack.length/this.bufferLength))} %) | Last Backup: ${this.lastBackedUp?moment(this.lastBackedUp).format('LLL'):"never!"}`
        console.log(this.isBackingUp?chalk.bold.yellow(message):message)
        if (this.stack.length >= this.bufferLength && !this.isBackingUp){
            this.initBackup()
        }
    }

    init() {
        this.watch = chokidar.watch(this.watchPath, { awaitWriteFinish: true })
        console.log(this.watchPath)
        chokidar.watch(this.watchPath, { awaitWriteFinish: true }).on('add', function(name) {
            const fileName = name.split('/').pop()
            this.add(fileName) 
        })
    }

    getAll() {
        return this.stack
    }
}

const autoBackup = new fileBackupQueue({ bufferLength: BACKUP_BUFFER, watchPath: WATCH_PATH, backupPath: BACKUP_LOCATIONS })
autoBackup.init()
