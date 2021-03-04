create database if not exists MyDatabase;
USE MyDatabase;


Drop table if exists StudentRecord;

CREATE TABLE `MyDatabase`.`StudentRecord` (
`Id` VARCHAR(45) NOT NULL,
`Name` VARCHAR(45) NULL,
`Image` LONGBLOB NULL,
`Email` VARCHAR(45) NULL,
`DOB` VARCHAR(45) NULL,
PRIMARY KEY (`Id`));

Drop table if exists TeacherRecord;
CREATE TABLE `MyDatabase`.`TeacherRecord` (
`TeacherName` VARCHAR(45) NOT NULL,
`Email` VARCHAR(45) NULL,
`password` VARCHAR(45) NULL,
PRIMARY KEY (`TeacherName`)) ;


Drop table if exists TeacherClasses;
CREATE TABLE `MyDatabase`.`TeacherClasses` (
`TeacherName` VARCHAR(45) NULL,
`ClassName` VARCHAR(45) NULL);

exit
