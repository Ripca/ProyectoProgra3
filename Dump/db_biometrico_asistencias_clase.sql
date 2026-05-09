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
-- Table structure for table `asistencias_clase`
--

DROP TABLE IF EXISTS `asistencias_clase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `asistencias_clase` (
  `id` int NOT NULL AUTO_INCREMENT,
  `persona_id` int NOT NULL,
  `curso_id` int NOT NULL,
  `salon_id` int NOT NULL,
  `fecha_hora` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `metodo` enum('BIOMETRICO','MANUAL') NOT NULL DEFAULT 'BIOMETRICO',
  `confirmado_por` int DEFAULT NULL,
  `observacion` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_asistencias_salon` (`salon_id`),
  KEY `fk_asistencias_confirmador` (`confirmado_por`),
  KEY `idx_asistencias_fecha` (`fecha_hora`),
  KEY `idx_asistencias_persona_fecha` (`persona_id`,`fecha_hora`),
  KEY `idx_asistencias_curso_fecha` (`curso_id`,`fecha_hora`),
  CONSTRAINT `fk_asistencias_confirmador` FOREIGN KEY (`confirmado_por`) REFERENCES `personas` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_asistencias_curso` FOREIGN KEY (`curso_id`) REFERENCES `cursos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_asistencias_persona` FOREIGN KEY (`persona_id`) REFERENCES `personas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_asistencias_salon` FOREIGN KEY (`salon_id`) REFERENCES `salones` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asistencias_clase`
--

LOCK TABLES `asistencias_clase` WRITE;
/*!40000 ALTER TABLE `asistencias_clase` DISABLE KEYS */;
INSERT INTO `asistencias_clase` VALUES (1,1,1,1,'2026-04-30 06:10:09','BIOMETRICO',NULL,NULL),(2,2,1,1,'2026-04-30 06:10:09','BIOMETRICO',NULL,NULL),(3,1,2,2,'2026-04-30 06:10:09','MANUAL',NULL,NULL),(4,1,1,1,'2026-04-30 06:10:18','BIOMETRICO',NULL,NULL),(5,2,1,1,'2026-04-30 06:10:18','BIOMETRICO',NULL,NULL),(6,1,2,2,'2026-04-30 06:10:18','MANUAL',NULL,NULL);
/*!40000 ALTER TABLE `asistencias_clase` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-01 22:38:43
