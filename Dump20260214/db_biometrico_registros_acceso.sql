CREATE DATABASE  IF NOT EXISTS `db_biometrico` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `db_biometrico`;
-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: localhost    Database: db_biometrico
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `registros_acceso`
--

DROP TABLE IF EXISTS `registros_acceso`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `registros_acceso` (
  `id` int NOT NULL AUTO_INCREMENT,
  `persona_id` int NOT NULL,
  `fecha_hora` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `ubicacion` varchar(50) DEFAULT NULL,
  `tipo_acceso` enum('puerta_principal','salon') NOT NULL,
  `salon` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `persona_id` (`persona_id`),
  CONSTRAINT `registros_acceso_ibfk_1` FOREIGN KEY (`persona_id`) REFERENCES `personas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `registros_acceso`
--

LOCK TABLES `registros_acceso` WRITE;
/*!40000 ALTER TABLE `registros_acceso` DISABLE KEYS */;
INSERT INTO `registros_acceso` VALUES (1,1,'2026-02-07 18:01:19','Puerta Principal','puerta_principal',NULL),(2,2,'2026-02-07 18:05:16','Puerta Principal','puerta_principal',NULL),(3,4,'2026-02-07 18:12:20','Entrada Principal','puerta_principal',NULL),(4,6,'2026-02-07 18:12:20','Entrada Principal','puerta_principal',NULL),(5,6,'2026-02-07 18:12:20','Laboratorio 1','salon','LAB-1'),(6,11,'2026-02-07 18:18:30','Puerta Principal','puerta_principal',NULL),(7,1,'2026-02-07 18:18:31','Puerta Principal','puerta_principal',NULL),(8,2,'2026-02-07 18:18:36','Puerta Principal','puerta_principal',NULL),(9,2,'2026-02-07 18:24:18','LAB-1','salon','LAB-1'),(10,11,'2026-02-07 18:24:21','LAB-1','salon','LAB-1'),(11,1,'2026-02-07 18:24:24','LAB-1','salon','LAB-1'),(12,1,'2026-02-14 23:39:49','Entrada Principal','puerta_principal',NULL),(13,11,'2026-02-14 23:39:53','Entrada Principal','puerta_principal',NULL),(14,2,'2026-02-14 23:39:55','Entrada Principal','puerta_principal',NULL),(15,1,'2026-02-14 23:45:38','Entrada Principal','puerta_principal',NULL),(16,2,'2026-02-14 23:45:39','Entrada Principal','puerta_principal',NULL),(17,11,'2026-02-14 23:46:03','Entrada Principal','puerta_principal',NULL);
/*!40000 ALTER TABLE `registros_acceso` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-14 17:47:42
