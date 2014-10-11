-- MySQL dump 10.13  Distrib 5.5.38, for debian-linux-gnu (armv7l)
--
-- Host: localhost    Database: templogger
-- ------------------------------------------------------
-- Server version	5.5.38-0+wheezy1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `config`
--

DROP TABLE IF EXISTS `config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `config` (
  `target` varchar(64) NOT NULL,
  `attribute` varchar(64) NOT NULL,
  `op` char(1) DEFAULT NULL,
  `value` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`target`,`attribute`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `config`
--

LOCK TABLES `config` WRITE;
/*!40000 ALTER TABLE `config` DISABLE KEYS */;
INSERT INTO `config` VALUES ('0','max','>','30'),('1','max','=','26');
/*!40000 ALTER TABLE `config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `data`
--

DROP TABLE IF EXISTS `data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `data` (
  `probe_number` int(11) NOT NULL,
  `temperature` float DEFAULT NULL,
  `humidity` float DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `probe_number` (`probe_number`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `data`
--

LOCK TABLES `data` WRITE;
/*!40000 ALTER TABLE `data` DISABLE KEYS */;
INSERT INTO `data` VALUES (4,26.1,49.9,'2014-10-10 23:46:27'),(4,26.2,49.2,'2014-10-10 23:52:30'),(4,26.2,49,'2014-10-10 23:53:38'),(4,26.2,48.8,'2014-10-10 23:54:37'),(4,26.4,48.9,'2014-10-10 23:57:30'),(0,25.25,48.9,'2014-10-10 23:57:31'),(4,26.5,46.9,'2014-10-10 23:58:47'),(0,25.5,46.9,'2014-10-10 23:58:48'),(1,25.437,46.9,'2014-10-10 23:58:50'),(2,25.5,46.9,'2014-10-10 23:58:51'),(4,26.6,47,'2014-10-10 23:59:36'),(0,25.625,47,'2014-10-10 23:59:37'),(1,25.5,47,'2014-10-10 23:59:38'),(2,25.562,47,'2014-10-10 23:59:39'),(4,26.6,47.1,'2014-10-11 00:03:08'),(0,25.875,47.1,'2014-10-11 00:03:09'),(1,25.75,47.1,'2014-10-11 00:03:10'),(2,25.75,47.1,'2014-10-11 00:03:11'),(4,26.6,46.3,'2014-10-11 00:04:02'),(0,25.875,46.3,'2014-10-11 00:04:03'),(1,25.75,46.3,'2014-10-11 00:04:04'),(2,25.75,46.3,'2014-10-11 00:04:05'),(4,26.7,46.6,'2014-10-11 00:05:02'),(0,25.937,46.6,'2014-10-11 00:05:03'),(1,25.75,46.6,'2014-10-11 00:05:04'),(2,25.75,46.6,'2014-10-11 00:05:04'),(4,26.6,46.9,'2014-10-11 00:06:08'),(0,25.937,46.9,'2014-10-11 00:06:09'),(1,25.812,46.9,'2014-10-11 00:06:10'),(2,25.812,46.9,'2014-10-11 00:06:11'),(4,26.7,47,'2014-10-11 00:07:08'),(0,25.937,47,'2014-10-11 00:07:08'),(1,25.812,47,'2014-10-11 00:07:09'),(2,25.75,47,'2014-10-11 00:07:10');
/*!40000 ALTER TABLE `data` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2014-10-11  0:07:28
