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
-- Table structure for table `asignaciones_catedratico`
--

DROP TABLE IF EXISTS `asignaciones_catedratico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `asignaciones_catedratico` (
  `id` int NOT NULL AUTO_INCREMENT,
  `curso_id` int NOT NULL,
  `seccion_id` int NOT NULL,
  `catedratico_id` int NOT NULL,
  `salon_id` int NOT NULL,
  `dia_semana` enum('Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo') NOT NULL,
  `hora_inicio` time NOT NULL,
  `hora_fin` time NOT NULL,
  PRIMARY KEY (`id`),
  KEY `curso_id` (`curso_id`),
  KEY `seccion_id` (`seccion_id`),
  KEY `catedratico_id` (`catedratico_id`),
  KEY `salon_id` (`salon_id`),
  CONSTRAINT `asignaciones_catedratico_ibfk_1` FOREIGN KEY (`curso_id`) REFERENCES `cursos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `asignaciones_catedratico_ibfk_2` FOREIGN KEY (`seccion_id`) REFERENCES `secciones` (`id`) ON DELETE CASCADE,
  CONSTRAINT `asignaciones_catedratico_ibfk_3` FOREIGN KEY (`catedratico_id`) REFERENCES `personas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `asignaciones_catedratico_ibfk_4` FOREIGN KEY (`salon_id`) REFERENCES `salones` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asignaciones_catedratico`
--

LOCK TABLES `asignaciones_catedratico` WRITE;
/*!40000 ALTER TABLE `asignaciones_catedratico` DISABLE KEYS */;
INSERT INTO `asignaciones_catedratico` VALUES (1,1,1,1,1,'Lunes','18:00:00','20:00:00'),(2,1,2,1,2,'Martes','18:00:00','20:00:00'),(3,2,1,2,3,'Miércoles','20:00:00','21:30:00'),(4,3,1,3,5,'Sábado','07:00:00','09:00:00');
/*!40000 ALTER TABLE `asignaciones_catedratico` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-01 22:38:42
