-- phpMyAdmin SQL Dump
-- version 3.4.11.1deb2+deb7u1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Oct 11, 2014 at 12:01 AM
-- Server version: 5.5.38
-- PHP Version: 5.4.4-14+deb7u14

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `templogger`
--

-- --------------------------------------------------------

--
-- Table structure for table `config`
--

CREATE TABLE IF NOT EXISTS `config` (
  `target` varchar(64) NOT NULL,
  `attribute` varchar(64) NOT NULL,
  `op` char(1) DEFAULT NULL,
  `value` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`target`,`attribute`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `config`
--

INSERT INTO `config` (`target`, `attribute`, `op`, `value`) VALUES
('0', 'max', '>', '30'),
('1', 'max', '=', '26');

-- --------------------------------------------------------

--
-- Table structure for table `data`
--

CREATE TABLE IF NOT EXISTS `data` (
  `probe_number` int(11) NOT NULL,
  `temperature` float DEFAULT NULL,
  `humidity` float DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `probe_number` (`probe_number`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `data`
--

INSERT INTO `data` (`probe_number`, `temperature`, `humidity`, `timestamp`) VALUES
(4, 26.1, 49.9, '2014-10-10 23:46:27'),
(4, 26.2, 49.2, '2014-10-10 23:52:30'),
(4, 26.2, 49, '2014-10-10 23:53:38'),
(4, 26.2, 48.8, '2014-10-10 23:54:37'),
(4, 26.4, 48.9, '2014-10-10 23:57:30'),
(0, 25.25, 48.9, '2014-10-10 23:57:31'),
(4, 26.5, 46.9, '2014-10-10 23:58:47'),
(0, 25.5, 46.9, '2014-10-10 23:58:48'),
(1, 25.437, 46.9, '2014-10-10 23:58:50'),
(2, 25.5, 46.9, '2014-10-10 23:58:51'),
(4, 26.6, 47, '2014-10-10 23:59:36'),
(0, 25.625, 47, '2014-10-10 23:59:37'),
(1, 25.5, 47, '2014-10-10 23:59:38'),
(2, 25.562, 47, '2014-10-10 23:59:39');

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
