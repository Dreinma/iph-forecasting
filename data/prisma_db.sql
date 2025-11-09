-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Nov 03, 2025 at 08:47 AM
-- Server version: 8.0.30
-- PHP Version: 8.1.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `prisma_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `activity_logs`
--

CREATE TABLE `activity_logs` (
  `id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `entity_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `entity_id` int DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip_address` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_agent` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `admin_users`
--

CREATE TABLE `admin_users` (
  `id` int NOT NULL,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `last_login` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `admin_users`
--

INSERT INTO `admin_users` (`id`, `username`, `password_hash`, `email`, `is_active`, `created_at`, `last_login`) VALUES
(1, 'admin', '$2b$12$uE7VSBbslVeg.tcZSfaa9e.XeYSDz/Ab8nYzXXcmbOxRXStLs7LwG', 'admin@prisma.local', 1, '2025-11-01 11:04:06', '2025-11-01 11:51:53');

-- --------------------------------------------------------

--
-- Table structure for table `alert_history`
--

CREATE TABLE `alert_history` (
  `id` int NOT NULL,
  `alert_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `severity` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `message` text COLLATE utf8mb4_unicode_ci,
  `value` float DEFAULT NULL,
  `threshold` float DEFAULT NULL,
  `acknowledged` tinyint(1) DEFAULT NULL,
  `acknowledged_at` datetime DEFAULT NULL,
  `acknowledged_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_by_system` tinyint(1) DEFAULT NULL,
  `admin_notes` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `alert_rules`
--

CREATE TABLE `alert_rules` (
  `id` int NOT NULL,
  `rule_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rule_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `threshold_value` float DEFAULT NULL,
  `comparison_operator` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `severity_level` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `check_period_days` int DEFAULT NULL,
  `min_data_points` int DEFAULT NULL,
  `created_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `alert_rules`
--

INSERT INTO `alert_rules` (`id`, `rule_name`, `rule_type`, `is_active`, `threshold_value`, `comparison_operator`, `severity_level`, `check_period_days`, `min_data_points`, `created_by`, `created_at`, `updated_at`, `description`) VALUES
(1, 'IPH Tinggi - 2 Sigma', 'threshold', 1, 2, '>', 'warning', 7, 5, 'system', '2025-11-01 11:04:06', '2025-11-01 11:04:06', 'Alert when IPH > 2 sigma'),
(2, 'IPH Kritis - 3 Sigma', 'threshold', 1, 3, '>', 'critical', 7, 5, 'system', '2025-11-01 11:04:06', '2025-11-01 11:04:06', 'Critical alert when IPH > 3 sigma');

-- --------------------------------------------------------

--
-- Table structure for table `commodity_data`
--

CREATE TABLE `commodity_data` (
  `id` int NOT NULL,
  `tanggal` date NOT NULL,
  `bulan` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `minggu` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tahun` int DEFAULT NULL,
  `kab_kota` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `iph_id` int DEFAULT NULL,
  `iph_value` float DEFAULT NULL,
  `komoditas_andil` text COLLATE utf8mb4_unicode_ci,
  `komoditas_fluktuasi` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nilai_fluktuasi` float DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `commodity_data`
--

INSERT INTO `commodity_data` (`id`, `tanggal`, `bulan`, `minggu`, `tahun`, `kab_kota`, `iph_id`, `iph_value`, `komoditas_andil`, `komoditas_fluktuasi`, `nilai_fluktuasi`, `created_at`, `updated_at`) VALUES
(1, '2023-01-01', 'Januari\'23', 'M1', 2023, 'BATU', 1, -1.34, 'TELUR AYAM RAS(-0,773);PISANG(-0,333);DAGING AYAM RAS(-0,287)', 'CABAI RAWIT', 0.0553, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(2, '2023-01-08', 'Januari\'23', 'M2', 2023, 'BATU', 2, 0.93, 'CABAI RAWIT(0,063);MINYAK GORENG(0,054);CABAI MERAH(0,019)', 'IKAN KEMBUNG/IKAN GEMBUNG/ IKAN BANYAR/IKAN GEMBOLO/ IKAN ASO-ASO', 0.0329914, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(3, '2023-02-08', 'Februari\'23\'23', 'M1', 2023, 'BATU', 3, 1.36, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(4, '2023-02-15', 'Februari\'23\'23', 'M1', 2023, 'BATU', 4, 1.82, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(5, '2023-02-22', 'Februari\'23\'23', 'M1', 2023, 'BATU', 5, 2.18, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(6, '2023-03-01', 'Maret\'23\'23', 'M1', 2023, 'BATU', 6, -1.27, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(7, '2023-03-08', 'Maret\'23\'23', 'M1', 2023, 'BATU', 7, -1.49, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(8, '2023-03-15', 'Maret\'23\'23', 'M1', 2023, 'BATU', 8, -1.06, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(9, '2023-03-22', 'Maret\'23\'23', 'M1', 2023, 'BATU', 9, -0.83, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(10, '2023-03-29', 'Maret\'23\'23', 'M1', 2023, 'BATU', 10, -0.853, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(11, '2023-04-01', 'April\'23\'23', 'M1', 2023, 'BATU', 11, -1.786, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(12, '2023-04-08', 'April\'23\'23', 'M1', 2023, 'BATU', 12, -1.786, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(13, '2023-04-22', 'April\'23\'23', 'M1', 2023, 'BATU', 13, -1.786, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(14, '2023-05-01', 'Mei', 'M1', 2023, 'BATU', 14, 0.189, 'DAGING AYAM RAS(1,767);BERAS(0,627);MIE KERING INSTANT(0)', 'STABIL', NULL, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(15, '2023-05-08', 'Mei', 'M2', 2023, 'BATU', 15, 0.508, 'DAGING AYAM RAS(1,606);BERAS(0,974);MINYAK GORENG(0,243)', 'BAWANG MERAH', 0.0364878, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(16, '2023-05-15', 'Mei', 'M3', 2023, 'BATU', 16, 0.718, 'DAGING AYAM RAS(1,435);BERAS(1,06);MINYAK GORENG(0,304)', 'CABAI RAWIT', 0.111518, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(17, '2023-05-22', 'Mei', 'M4', 2023, 'BATU', 17, 1.258, 'DAGING AYAM RAS(1,527);BERAS(1,114);MINYAK GORENG(0,342)', 'CABAI RAWIT', 0.135153, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(18, '2023-05-29', 'Mei', 'M5', 2023, 'BATU', 18, 1.536, 'DAGING AYAM RAS(1,561);BERAS(1,134);MINYAK GORENG(0,357)', 'CABAI RAWIT', 0.212907, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(19, '2023-06-01', 'Juni\'23\'23', 'M1', 2023, 'BATU', 19, 1.655, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(20, '2023-06-08', 'Juni\'23\'23', 'M1', 2023, 'BATU', 20, 1.649, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(21, '2023-06-15', 'Juni\'23\'23', 'M1', 2023, 'BATU', 21, 1.644, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(22, '2023-06-22', 'Juni\'23\'23', 'M1', 2023, 'BATU', 22, 1.071, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(23, '2023-07-01', 'Juli\'23\'23', 'M1', 2023, 'BATU', 23, -0.02, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(24, '2023-07-08', 'Juli\'23\'23', 'M1', 2023, 'BATU', 24, 0.115, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(25, '2023-07-15', 'Juli\'23\'23', 'M1', 2023, 'BATU', 25, 0.13, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(26, '2023-07-22', 'Juli\'23\'23', 'M1', 2023, 'BATU', 26, 0.093, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(27, '2023-08-01', 'Agustus\'23\'23', 'M1', 2023, 'BATU', 27, -0.03, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(28, '2023-08-08', 'Agustus\'23\'23', 'M1', 2023, 'BATU', 28, -0.737, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(29, '2023-08-15', 'Agustus\'23\'23', 'M1', 2023, 'BATU', 29, -0.888, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(30, '2023-08-22', 'Agustus\'23\'23', 'M1', 2023, 'BATU', 30, -0.9, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(31, '2023-09-01', 'September\'23\'23', 'M1', 2023, 'BATU', 31, -0.548, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(32, '2023-09-08', 'September\'23\'23', 'M1', 2023, 'BATU', 32, -0.6, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(33, '2023-09-15', 'September\'23\'23', 'M1', 2023, 'BATU', 33, -0.404, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(34, '2023-09-22', 'September\'23\'23', 'M1', 2023, 'BATU', 34, -0.37, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(35, '2023-10-01', 'Oktober\'23', 'M1', 2023, 'BATU', 35, 0.101, 'BERAS(0.438);GULA PASIR(0.045);TEMPE(0)', 'STABIL', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(36, '2023-10-08', 'Oktober\'23', 'M2', 2023, 'BATU', 36, 0.221, 'BERAS(0.438);CABAI RAWIT(0.096);GULA PASIR(0.045)', 'CABAI RAWIT', 0.0958266, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(37, '2023-10-15', 'Oktober\'23', 'M3', 2023, 'BATU', 37, 0.323, 'BERAS(0.438);CABAI RAWIT(0.19);GULA PASIR(0.045)', 'CABAI RAWIT', 0.140859, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(38, '2023-10-22', 'Oktober\'23', 'M4', 2023, 'BATU', 38, 0.363, 'BERAS(0.438);CABAI RAWIT(0.283);GULA PASIR(0.045)', 'CABAI RAWIT', 0.176474, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(39, '2023-11-01', 'November\'23\'23', 'M1', 2023, 'BATU', 39, 0.672, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(40, '2023-11-08', 'November\'23\'23', 'M1', 2023, 'BATU', 40, 0.887, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(41, '2023-11-15', 'November\'23\'23', 'M1', 2023, 'BATU', 41, 1.534, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(42, '2023-11-22', 'November\'23\'23', 'M1', 2023, 'BATU', 42, 2.077, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(43, '2023-12-01', 'Desember\'23\'23', 'M1', 2023, 'BATU', 43, 2.021, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(44, '2023-12-08', 'Desember\'23\'23', 'M1', 2023, 'BATU', 44, 2.414, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(45, '2023-12-15', 'Desember\'23\'23', 'M1', 2023, 'BATU', 45, 2.414, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(46, '2023-12-22', 'Desember\'23\'23', 'M1', 2023, 'BATU', 46, 2.288, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(47, '2024-01-01', 'Januari', 'M1', 2024, 'BATU', 47, 0.166, 'DAGING SAPI(0.716);BAWANG PUTIH(0.126);BAWANG MERAH(0.053)', 'CABAI MERAH', 0.0524864, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(48, '2024-01-08', 'Januari', 'M2', 2024, 'BATU', 48, -0.746, 'CABAI MERAH(-0.977);CABAI RAWIT(-0.393);TELUR AYAM RAS(-0.042)', 'CABAI RAWIT', 0.0633677, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(49, '2024-01-15', 'Januari', 'M3', 2024, 'BATU', 49, -1.6, 'CABAI RAWIT(-1.0273), CABAI MERAH(-0.9684), DAGING AYAM RAS(-0.0618)', 'CABAI RAWIT', 0.2, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(50, '2024-01-22', 'Januari', 'M4', 2024, 'BATU', 50, -2.137, 'CABAI RAWIT(-1.409);CABAI MERAH(-0.96);DAGING AYAM RAS(-0.098)', 'CABAI RAWIT', 0.243442, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(51, '2024-02-01', 'Februari\'24\'24', 'M1', 2024, 'BATU', 51, -2.694, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(52, '2024-02-08', 'Februari\'24\'24', 'M1', 2024, 'BATU', 52, -2.328, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(53, '2024-02-15', 'Februari\'24\'24', 'M1', 2024, 'BATU', 53, -1.962, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(54, '2024-02-22', 'Februari\'24\'24', 'M1', 2024, 'BATU', 54, 0.355, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(55, '2024-02-29', 'Februari\'24\'24', 'M1', 2024, 'BATU', 55, 1.492, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(56, '2024-03-01', 'Maret\'24\'24', 'M1', 2024, 'BATU', 56, 4.523, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(57, '2024-03-08', 'Maret\'24\'24', 'M1', 2024, 'BATU', 57, 4.793, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(58, '2024-03-15', 'Maret\'24\'24', 'M1', 2024, 'BATU', 58, 4.489, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(59, '2024-03-22', 'Maret\'24\'24', 'M1', 2024, 'BATU', 59, 3.92, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(60, '2024-04-01', 'April', 'M1', 2024, 'BATU', 60, -3.69, 'CABAI MERAH(-1.1446), BERAS(-0.9792), CABAI RAWIT(-0.8677)', 'CABAI RAWIT', 0.09, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(61, '2024-04-15', 'April', 'M3', 2024, 'BATU', 61, -3.38, 'BERAS(-1.2585), CABAI MERAH(-1.1175), CABAI RAWIT(-0.7906)', 'BAWANG MERAH', 0.165876, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(62, '2024-04-22', 'April', 'M4', 2024, 'BATU', 62, -3.43, 'BERAS(-1.3819), CABAI MERAH(-1.1503), CABAI RAWIT(-0.8411)', 'BAWANG MERAH', 0.1816, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(63, '2024-05-01', 'Mei\'24\'24', 'M1', 2024, 'BATU', 63, 1.58, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(64, '2024-05-08', 'Mei\'24\'24', 'M1', 2024, 'BATU', 64, 1.81, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(65, '2024-05-15', 'Mei\'24\'24', 'M1', 2024, 'BATU', 65, 2.08, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(66, '2024-05-22', 'Mei\'24\'24', 'M1', 2024, 'BATU', 66, 1.89, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(67, '2024-05-29', 'Mei\'24\'24', 'M1', 2024, 'BATU', 67, 1.5, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(68, '2024-06-01', 'Juni\'24\'24', 'M1', 2024, 'BATU', 68, -2.15, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(69, '2024-06-15', 'Juni\'24\'24', 'M1', 2024, 'BATU', 69, -1.99, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(70, '2024-06-22', 'Juni\'24\'24', 'M1', 2024, 'BATU', 70, -2, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(71, '2024-07-01', 'Juli', 'M1', 2024, 'BATU', 71, -1.16, 'CABAI MERAH(-0.4619), BAWANG MERAH(-0.4465), BAWANG PUTIH(-0.1463)', 'STABIL', NULL, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(72, '2024-07-08', 'Juli', 'M2', 2024, 'BATU', 72, -1.19, 'BAWANG MERAH(-0.5476) , CABAI MERAH(-0.4662), BAWANG PUTIH(-0.1463)', 'CABAI RAWIT', 0.0958266, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(73, '2024-07-15', 'Juli', 'M3', 2024, 'BATU', 73, -1.09, 'BAWANG MERAH(-0.6359), CABAI MERAH(-0.5629), BAWANG PUTIH(-0.1463)', 'CABAI RAWIT', 0.232816, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(74, '2024-07-22', 'Juli', 'M4', 2024, 'BATU', 74, -0.84, 'BAWANG MERAH(-0.6789), CABAI MERAH(-0.6206), BAWANG PUTIH(-0.1463)', 'CABAI RAWIT', 0.276636, '2025-10-26 07:53:51', '2025-11-01 09:25:51'),
(75, '2024-09-01', 'September\'24', 'M1', 2024, 'BATU', 80, -2.58, 'CABAI RAWIT(-1.4922), DAGING SAPI(-0.3546), CABAI MERAH(-0.3118)', 'CABAI MERAH', 0.0502498, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(76, '2024-09-08', 'September\'24', 'M2', 2024, 'BATU', 81, -2.88, 'CABAI RAWIT(-1.5257), CABAI MERAH(-0.4384), DAGING SAPI(-0.3546)', 'CABAI MERAH', 0.080713, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(77, '2024-09-15', 'September\'24', 'M3', 2024, 'BATU', 82, -3.05, 'CABAI RAWIT(-1.5352), CABAI MERAH(-0.5281), DAGING SAPI(-0.3546)', 'CABAI MERAH', 0.108181, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(78, '2024-09-22', 'September\'24', 'M4', 2024, 'BATU', 83, -3.03, 'CABAI RAWIT(-1.5415), CABAI MERAH(-0.5846), DAGING SAPI(-0.3546)', 'CABAI MERAH', 0.111608, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(79, '2024-10-01', 'Oktober\'24\'24', 'M1', 2024, 'BATU', 84, -0.03, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(80, '2024-11-01', 'November\'24\'24', 'M1', 2024, 'BATU', 89, 0.78, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(81, '2024-12-01', 'Desember\'24', 'M1', 2024, 'BATU', 93, 0.14, 'BAWANG MERAH(0.4769), PISANG(0.0365), TEPUNG TERIGU(0.0273)', 'BERAS', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(82, '2024-12-08', 'Desember\'24', 'M2', 2024, 'BATU', 94, 0.36, 'BAWANG MERAH(0.4769), DAGING AYAM RAS(0.0391), PISANG(0.0365)', 'CABAI MERAH', 0.0335323, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(83, '2024-12-15', 'Desember\'24', 'M3', 2024, 'BATU', 95, 0.71, 'BAWANG MERAH(0.4769), CABAI MERAH(0.1362), DAGING AYAM RAS(0.0965)', 'CABAI MERAH', 0.109, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(84, '2024-12-22', 'Desember\'24', 'M4', 2024, 'BATU', 96, 1.04, 'BAWANG MERAH(0.4903), CABAI MERAH(0.2348), DAGING AYAM RAS(0.1158)', 'CABAI MERAH', 0.194487, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(85, '2025-04-08', 'April\'25\'25', 'M1', 2025, 'BATU', 108, -1.07, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(86, '2025-04-15', 'April\'25\'25', 'M1', 2025, 'BATU', 109, -1.31, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(87, '2025-05-15', 'Mei\'25\'25', 'M1', 2025, 'BATU', 112, -2.61, 'DATA_TIDAK_TERSEDIA', 'TIDAK_ADA_DATA', NULL, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(88, '2025-06-01', 'Juni\'25', 'M1', 2025, 'BATU', 115, -1.1, 'CABAI RAWIT(-0.3501), BAWANG MERAH(-0.2951), CABAI MERAH(-0.2162)', 'CABAI RAWIT', 0.104973, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(89, '2025-06-08', 'Juni\'25', 'M2', 2025, 'BATU', 116, -0.86, 'BAWANG PUTIH(-0.3336), BAWANG MERAH(-0.2951), CABAI RAWIT(-0.2626)', 'CABAI MERAH', 0.0866387, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(90, '2025-06-15', 'Juni\'25', 'M3', 2025, 'BATU', 117, -0.66, 'BAWANG PUTIH(-0.396), BAWANG MERAH(-0.2503), CABAI RAWIT(-0.0854)', 'CABAI RAWIT', 0.143044, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(91, '2025-06-22', 'Juni\'25', 'M4', 2025, 'BATU', 118, -0.43, 'BAWANG PUTIH(-0.4191), BAWANG MERAH(-0.1707), CABAI MERAH(-0.1261)', 'CABAI RAWIT', 0.18124, '2025-10-26 07:53:51', '2025-10-26 07:53:51'),
(92, '2024-08-05', 'Agustus', 'M1', 2024, 'BATU', 75, 0.76, 'CABAI RAWIT(1.4753), DAGING SAPI(0.2909), MINYAK GORENG(0.0501)', 'CABAI RAWIT', 0.0480458, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(93, '2024-08-12', 'Agustus', 'M2', 2024, 'BATU', 76, 1.01, 'CABAI RAWIT(1.6932), DAGING SAPI(0.2909), MINYAK GORENG(0.07)', 'CABAI MERAH', 0.0856133, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(94, '2024-08-19', 'Agustus', 'M3', 2024, 'BATU', 77, 1.05, 'CABAI RAWIT(1.6665), DAGING SAPI(0.2909), MINYAK GORENG(0.162)', 'CABAI MERAH', 0.0778455, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(95, '2024-08-26', 'Agustus', 'M4', 2024, 'BATU', 78, 0.81, 'CABAI RAWIT(1.4684), DAGING SAPI(0.2909), MINYAK GORENG(0.1739)', 'CABAI RAWIT', 0.0996702, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(96, '2024-09-02', 'Agustus', 'M5', 2024, 'BATU', 79, 0.35, 'CABAI RAWIT(1.1936), DAGING SAPI(0.2009), MINYAK GORENG(0.157)', 'CABAI RAWIT', 0.165496, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(97, '2024-10-14', 'Oktober', 'M2', 2024, 'BATU', 85, -0.1, 'CABAI MERAH(-0.1993), BERAS(-0.1514), DAGING AYAM RAS(-0.0754)', 'CABAI MERAH', 0.0319422, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(98, '2024-10-21', 'Oktober', 'M3', 2024, 'BATU', 86, -0.06, 'CABAI MERAH(-0.2207), BERAS(-0.1845), DAGING AYAM RAS(-0.0563)', 'CABAI RAWIT', 0.0395635, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(99, '2024-10-28', 'Oktober', 'M4', 2024, 'BATU', 87, 0.02, 'BAWANG MERAH(0.2054), BAWANG PUTIH(0.1138), CABAI RAWIT(0.0684)', 'CABAI MERAH', 0.0475959, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(100, '2024-11-04', 'Oktober', 'M5', 2024, 'BATU', 88, 0.19, 'BAWANG MERAH(0.2448), DAGING AYAM RAS(0.1621), BAWANG PUTIH(0.1318)', 'CABAI MERAH', 0.049422, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(101, '2024-11-11', 'November', 'M2', 2024, 'BATU', 90, 0.64, 'DAGING AYAM RAS(0.485), BAWANG MERAH(0.3708), BAWANG PUTIH(0.073)', 'DAGING AYAM RAS', 0.0157327, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(102, '2024-11-18', 'November', 'M3', 2024, 'BATU', 91, 0.7, 'BAWANG MERAH(0.4372), DAGING AYAM RAS(0.4369), BAWANG PUTIH(0.073)', 'BAWANG MERAH', 0.0430544, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(103, '2024-11-25', 'November', 'M4', 2024, 'BATU', 92, 0.72, 'BAWANG MERAH(0.5056), DAGING AYAM RAS(0.4167), BAWANG PUTIH(0.073)', 'BAWANG MERAH', 0.0702, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(104, '2025-01-06', 'Januari', 'M1', 2025, 'BATU', 97, 3.51, 'CABAI RAWIT(1.2828), CABAI MERAH(1.238), TELUR AYAM RAS(0.5421)', 'CABAI MERAH', 0.03175, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(105, '2025-01-13', 'Januari', 'M2', 2025, 'BATU', 98, 4.26, 'CABAI RAWIT(1.8586), CABAI MERAH(1.4167), TELUR AYAM RAS(0.5421)', 'CABAI RAWIT', 0.180507, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(106, '2025-01-20', 'Januari', 'M3', 2025, 'BATU', 99, 4.84, 'CABAI RAWIT(2.3236), CABAI MERAH(1.5249), TELUR AYAM RAS(0.5421)', 'CABAI RAWIT', 0.205224, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(107, '2025-01-27', 'Januari', 'M4', 2025, 'BATU', 100, 4.87, 'CABAI RAWIT(2.3614), CABAI MERAH(1.6554), TELUR AYAM RAS(0.3905)', 'CABAI RAWIT', 0.170342, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(108, '2025-02-03', 'Februari', 'M1', 2025, 'BATU', 101, -1.04, 'TELUR AYAM RAS(-0.5918), CABAI RAWIT(-0.4772), DAGING AYAM RAS(-0.271)', 'BAWANG MERAH', 0.03402, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(109, '2025-02-10', 'Februari', 'M2', 2025, 'BATU', 102, -1.17, 'CABAI RAWIT(-0.5435), TELUR AYAM RAS(-0.5007), BAWANG MERAH(-0.3452)', 'BAWANG MERAH', 0.0440617, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(110, '2025-02-17', 'Februari', 'M3', 2025, 'BATU', 103, -1.45, 'CABAI RAWIT(-0.6456), TELUR AYAM RAS(-0.458), BAWANG MERAH(-0.3995)', 'CABAI MERAH', 0.0965311, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(111, '2025-02-24', 'Februari', 'M4', 2025, 'BATU', 104, -1.14, 'BAWANG MERAH(-0.4262), CABAI RAWIT(-0.4238), TELUR AYAM RAS(-0.3568)', 'CABAI RAWIT', 0.137639, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(112, '2025-03-03', 'Maret', 'M1', 2025, 'BATU', 105, 3.03, 'CABAI RAWIT(1.8718), CABAI MERAH(0.4241), TELUR AYAM RAS(0.3209)', 'CABAI RAWIT', 0.0538812, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(113, '2025-03-10', 'Maret', 'M2', 2025, 'BATU', 106, 2.29, 'CABAI RAWIT(1.4945), TELUR AYAM RAS(0.302), DAGING AYAM RAS(0.2742)', 'CABAI MERAH', 0.144374, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(114, '2025-03-17', 'Maret', 'M3', 2025, 'BATU', 107, 2.28, 'CABAI RAWIT(1.5765), DAGING AYAM RAS(0.2742), TELUR AYAM RAS(0.2456)', 'CABAI MERAH', 0.14979, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(115, '2025-04-21', 'April', 'M3', 2025, 'BATU', 110, -1.31, 'CABAI RAWIT(-0.7864), DAGING AYAM RAS(-0.4857), TELUR AYAM RAS(-0.3199)', 'CABAI RAWIT', 0.0600184, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(116, '2025-05-05', 'Mei', 'M1', 2025, 'BATU', 111, -2.24, 'CABAI RAWIT(-1.3317), DAGING AYAM RAS(-0.5126), CABAI MERAH(-0.2092)', 'CABAI MERAH', 0.0338983, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(117, '2025-05-19', 'Mei', 'M3', 2025, 'BATU', 113, -2.61, 'CABAI RAWIT(-1.5893), DAGING AYAM RAS(-0.445), CABAI MERAH(-0.369)', 'CABAI RAWIT', 0.0857354, '2025-11-01 09:26:16', '2025-11-01 09:26:16'),
(118, '2025-05-26', 'Mei', 'M4', 2025, 'BATU', 114, -2.81, 'CABAI RAWIT(-1.7288), CABAI MERAH(-0.471), DAGING AYAM RAS(-0.338)', 'CABAI RAWIT', 0.120344, '2025-11-01 09:26:16', '2025-11-01 09:26:16');

-- --------------------------------------------------------

--
-- Table structure for table `forecast_history`
--

CREATE TABLE `forecast_history` (
  `id` int NOT NULL,
  `model_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `weeks_forecasted` int NOT NULL,
  `avg_prediction` float DEFAULT NULL,
  `trend` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `volatility` float DEFAULT NULL,
  `min_prediction` float DEFAULT NULL,
  `max_prediction` float DEFAULT NULL,
  `model_mae` float DEFAULT NULL,
  `model_rmse` float DEFAULT NULL,
  `model_r2` float DEFAULT NULL,
  `forecast_data` text COLLATE utf8mb4_unicode_ci,
  `created_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `forecast_history`
--

INSERT INTO `forecast_history` (`id`, `model_name`, `weeks_forecasted`, `avg_prediction`, `trend`, `volatility`, `min_prediction`, `max_prediction`, `model_mae`, `model_rmse`, `model_r2`, `forecast_data`, `created_by`, `created_at`) VALUES
(1, 'XGBoost_Advanced', 8, -0.749768, 'Naik', 0.030103, -0.790891, -0.677814, 0.873866, 1.2146, 0.656833, '[{\"date\": \"2025-06-29\", \"prediction\": -0.768332302570343, \"lower_bound\": -1.0460414308860744, \"upper_bound\": -0.49062317425461166, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-06\", \"prediction\": -0.790890634059906, \"lower_bound\": -1.1091926914882007, \"upper_bound\": -0.4725885766316113, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-13\", \"prediction\": -0.6778144240379333, \"lower_bound\": -1.0272645314954147, \"upper_bound\": -0.328364316580452, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-20\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.1284964799240078, \"upper_bound\": -0.377078223292545, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-27\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.151631141718987, \"upper_bound\": -0.3539435614975656, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-03\", \"prediction\": -0.7499613761901855, \"lower_bound\": -1.1697204992986683, \"upper_bound\": -0.33020225308170276, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-10\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.1917801084083377, \"upper_bound\": -0.3137945948082151, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-17\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.2096823381491344, \"upper_bound\": -0.29589236506741834, \"confidence\": 0.758915269519338}]', 'system', '2025-11-01 12:15:03'),
(2, 'XGBoost_Advanced', 8, -0.749768, 'Naik', 0.030103, -0.790891, -0.677814, 0.873866, 1.2146, 0.656833, '[{\"date\": \"2025-06-29\", \"prediction\": -0.768332302570343, \"lower_bound\": -1.0460414308860744, \"upper_bound\": -0.49062317425461166, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-06\", \"prediction\": -0.790890634059906, \"lower_bound\": -1.1091926914882007, \"upper_bound\": -0.4725885766316113, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-13\", \"prediction\": -0.6778144240379333, \"lower_bound\": -1.0272645314954147, \"upper_bound\": -0.328364316580452, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-20\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.1284964799240078, \"upper_bound\": -0.377078223292545, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-27\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.151631141718987, \"upper_bound\": -0.3539435614975656, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-03\", \"prediction\": -0.7499613761901855, \"lower_bound\": -1.1697204992986683, \"upper_bound\": -0.33020225308170276, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-10\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.1917801084083377, \"upper_bound\": -0.3137945948082151, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-17\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.2096823381491344, \"upper_bound\": -0.29589236506741834, \"confidence\": 0.758915269519338}]', 'system', '2025-11-01 12:15:04'),
(3, 'XGBoost_Advanced', 8, -0.749768, 'Naik', 0.030103, -0.790891, -0.677814, 0.873866, 1.2146, 0.656833, '[{\"date\": \"2025-06-29\", \"prediction\": -0.768332302570343, \"lower_bound\": -1.0460414308860744, \"upper_bound\": -0.49062317425461166, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-06\", \"prediction\": -0.790890634059906, \"lower_bound\": -1.1091926914882007, \"upper_bound\": -0.4725885766316113, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-13\", \"prediction\": -0.6778144240379333, \"lower_bound\": -1.0272645314954147, \"upper_bound\": -0.328364316580452, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-20\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.1284964799240078, \"upper_bound\": -0.377078223292545, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-27\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.151631141718987, \"upper_bound\": -0.3539435614975656, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-03\", \"prediction\": -0.7499613761901855, \"lower_bound\": -1.1697204992986683, \"upper_bound\": -0.33020225308170276, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-10\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.1917801084083377, \"upper_bound\": -0.3137945948082151, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-17\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.2096823381491344, \"upper_bound\": -0.29589236506741834, \"confidence\": 0.758915269519338}]', 'system', '2025-11-01 12:21:28'),
(4, 'XGBoost_Advanced', 8, -0.749768, 'Naik', 0.030103, -0.790891, -0.677814, 0.873866, 1.2146, 0.656833, '[{\"date\": \"2025-06-29\", \"prediction\": -0.768332302570343, \"lower_bound\": -1.0460414308860744, \"upper_bound\": -0.49062317425461166, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-06\", \"prediction\": -0.790890634059906, \"lower_bound\": -1.1091926914882007, \"upper_bound\": -0.4725885766316113, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-13\", \"prediction\": -0.6778144240379333, \"lower_bound\": -1.0272645314954147, \"upper_bound\": -0.328364316580452, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-20\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.1284964799240078, \"upper_bound\": -0.377078223292545, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-27\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.151631141718987, \"upper_bound\": -0.3539435614975656, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-03\", \"prediction\": -0.7499613761901855, \"lower_bound\": -1.1697204992986683, \"upper_bound\": -0.33020225308170276, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-10\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.1917801084083377, \"upper_bound\": -0.3137945948082151, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-17\", \"prediction\": -0.7527873516082764, \"lower_bound\": -1.2096823381491344, \"upper_bound\": -0.29589236506741834, \"confidence\": 0.758915269519338}]', 'system', '2025-11-01 12:21:29'),
(5, 'LightGBM', 8, -0.664061, 'Naik', 0.0589323, -0.766496, -0.595112, 0.972012, 1.36788, 0.564753, '[{\"date\": \"2025-06-29\", \"prediction\": -0.7664963981097116, \"lower_bound\": -1.044205526425443, \"upper_bound\": -0.48878726979398024, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-06\", \"prediction\": -0.759929857161319, \"lower_bound\": -1.0782319145896138, \"upper_bound\": -0.4416277997330243, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-13\", \"prediction\": -0.5951120582487165, \"lower_bound\": -0.9445621657061978, \"upper_bound\": -0.24566195079123515, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-20\", \"prediction\": -0.6381907488518137, \"lower_bound\": -1.0138998771675451, \"upper_bound\": -0.2624816205360823, \"confidence\": 0.758915269519338}, {\"date\": \"2025-07-27\", \"prediction\": -0.6381907488518137, \"lower_bound\": -1.0370345389625244, \"upper_bound\": -0.23934695874110296, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-03\", \"prediction\": -0.6381907488518137, \"lower_bound\": -1.0579498719602964, \"upper_bound\": -0.21843162574333091, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-10\", \"prediction\": -0.6381907488518137, \"lower_bound\": -1.077183505651875, \"upper_bound\": -0.19919799205175243, \"confidence\": 0.758915269519338}, {\"date\": \"2025-08-17\", \"prediction\": -0.6381907488518137, \"lower_bound\": -1.0950857353926717, \"upper_bound\": -0.18129576231095568, \"confidence\": 0.758915269519338}]', 'system', '2025-11-01 12:22:47');

-- --------------------------------------------------------

--
-- Table structure for table `iph_data`
--

CREATE TABLE `iph_data` (
  `id` int NOT NULL,
  `tanggal` date NOT NULL,
  `indikator_harga` float NOT NULL,
  `bulan` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `minggu` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tahun` int DEFAULT NULL,
  `bulan_numerik` int DEFAULT NULL,
  `kab_kota` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `lag_1` float DEFAULT NULL,
  `lag_2` float DEFAULT NULL,
  `lag_3` float DEFAULT NULL,
  `lag_4` float DEFAULT NULL,
  `ma_3` float DEFAULT NULL,
  `ma_7` float DEFAULT NULL,
  `data_source` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `iph_data`
--

INSERT INTO `iph_data` (`id`, `tanggal`, `indikator_harga`, `bulan`, `minggu`, `tahun`, `bulan_numerik`, `kab_kota`, `lag_1`, `lag_2`, `lag_3`, `lag_4`, `ma_3`, `ma_7`, `data_source`, `created_at`, `updated_at`) VALUES
(1, '2023-01-01', -1.34, 'Januari\'23', NULL, 2023, 1, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(2, '2023-01-08', 0.93, 'Januari\'23', NULL, 2023, 1, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(3, '2023-02-08', 1.36, 'Februari\'23', NULL, 2023, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(4, '2023-02-15', 1.82, 'Februari\'23', NULL, 2023, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(5, '2023-02-22', 2.18, 'Februari\'23', NULL, 2023, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(6, '2023-03-01', -1.27, 'Maret\'23', NULL, 2023, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(7, '2023-03-08', -1.49, 'Maret\'23', NULL, 2023, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(8, '2023-03-15', -1.06, 'Maret\'23', NULL, 2023, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(9, '2023-03-22', -0.83, 'Maret\'23', NULL, 2023, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(10, '2023-03-29', -0.853, 'Maret\'23', NULL, 2023, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(11, '2023-04-01', -1.786, 'April\'23', NULL, 2023, 4, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(12, '2023-04-08', -1.786, 'April\'23', NULL, 2023, 4, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(13, '2023-04-22', -1.786, 'April\'23', NULL, 2023, 4, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(14, '2023-05-01', 0.189, 'Mei\'23', NULL, 2023, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(15, '2023-05-08', 0.508, 'Mei\'23', NULL, 2023, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(16, '2023-05-15', 0.718, 'Mei\'23', NULL, 2023, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(17, '2023-05-22', 1.258, 'Mei\'23', NULL, 2023, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(18, '2023-05-29', 1.536, 'Mei\'23', NULL, 2023, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(19, '2023-06-01', 1.655, 'Juni\'23', NULL, 2023, 6, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(20, '2023-06-08', 1.649, 'Juni\'23', NULL, 2023, 6, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(21, '2023-06-15', 1.644, 'Juni\'23', NULL, 2023, 6, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(22, '2023-06-22', 1.071, 'Juni\'23', NULL, 2023, 6, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(23, '2023-07-01', -0.02, 'Juli\'23', NULL, 2023, 7, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(24, '2023-07-08', 0.115, 'Juli\'23', NULL, 2023, 7, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(25, '2023-07-15', 0.13, 'Juli\'23', NULL, 2023, 7, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(26, '2023-07-22', 0.093, 'Juli\'23', NULL, 2023, 7, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(27, '2023-08-01', -0.03, 'Agustus\'23', NULL, 2023, 8, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(28, '2023-08-08', -0.737, 'Agustus\'23', NULL, 2023, 8, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(29, '2023-08-15', -0.888, 'Agustus\'23', NULL, 2023, 8, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(30, '2023-08-22', -0.9, 'Agustus\'23', NULL, 2023, 8, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(31, '2023-09-01', -0.548, 'September\'23', NULL, 2023, 9, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(32, '2023-09-08', -0.6, 'September\'23', NULL, 2023, 9, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(33, '2023-09-15', -0.404, 'September\'23', NULL, 2023, 9, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(34, '2023-09-22', -0.37, 'September\'23', NULL, 2023, 9, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(35, '2023-10-01', 0.101, 'Oktober\'23', NULL, 2023, 10, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(36, '2023-10-08', 0.221, 'Oktober\'23', NULL, 2023, 10, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(37, '2023-10-15', 0.323, 'Oktober\'23', NULL, 2023, 10, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(38, '2023-10-22', 0.363, 'Oktober\'23', NULL, 2023, 10, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(39, '2023-11-01', 0.672, 'November\'23', NULL, 2023, 11, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(40, '2023-11-08', 0.887, 'November\'23', NULL, 2023, 11, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(41, '2023-11-15', 1.534, 'November\'23', NULL, 2023, 11, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(42, '2023-11-22', 2.077, 'November\'23', NULL, 2023, 11, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(43, '2023-12-01', 2.021, 'Desember\'23', NULL, 2023, 12, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(44, '2023-12-08', 2.414, 'Desember\'23', NULL, 2023, 12, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(45, '2023-12-15', 2.414, 'Desember\'23', NULL, 2023, 12, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(46, '2023-12-22', 2.288, 'Desember\'23', NULL, 2023, 12, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(47, '2024-01-01', 0.166, 'Januari\'24', NULL, 2024, 1, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(48, '2024-01-08', -0.746, 'Januari\'24', NULL, 2024, 1, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(49, '2024-01-15', -1.6, 'Januari\'24', NULL, 2024, 1, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(50, '2024-01-22', -2.137, 'Januari\'24', NULL, 2024, 1, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(51, '2024-02-01', -2.694, 'Februari\'24', NULL, 2024, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(52, '2024-02-08', -2.328, 'Februari\'24', NULL, 2024, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(53, '2024-02-15', -1.962, 'Februari\'24', NULL, 2024, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(54, '2024-02-22', 0.355, 'Februari\'24', NULL, 2024, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(55, '2024-02-29', 1.492, 'Februari\'24', NULL, 2024, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(56, '2024-03-01', 4.523, 'Maret\'24', NULL, 2024, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(57, '2024-03-08', 4.793, 'Maret\'24', NULL, 2024, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(58, '2024-03-15', 4.489, 'Maret\'24', NULL, 2024, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(59, '2024-03-22', 3.92, 'Maret\'24', NULL, 2024, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(60, '2024-04-01', -3.69, 'April\'24', NULL, 2024, 4, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(61, '2024-04-15', -3.38, 'April\'24', NULL, 2024, 4, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(62, '2024-04-22', -3.43, 'April\'24', NULL, 2024, 4, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(63, '2024-05-01', 1.58, 'Mei\'24', NULL, 2024, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(64, '2024-05-08', 1.81, 'Mei\'24', NULL, 2024, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(65, '2024-05-15', 2.08, 'Mei\'24', NULL, 2024, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(66, '2024-05-22', 1.89, 'Mei\'24', NULL, 2024, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(67, '2024-05-29', 1.5, 'Mei\'24', NULL, 2024, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(68, '2024-06-01', -2.15, 'Juni\'24', NULL, 2024, 6, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(69, '2024-06-15', -1.99, 'Juni\'24', NULL, 2024, 6, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(70, '2024-06-22', -2, 'Juni\'24', NULL, 2024, 6, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(71, '2024-07-01', -1.16, 'Juli\'24', NULL, 2024, 7, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(72, '2024-07-08', -1.19, 'Juli\'24', NULL, 2024, 7, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(73, '2024-07-15', -1.09, 'Juli\'24', NULL, 2024, 7, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(74, '2024-07-22', -0.84, 'Juli\'24', NULL, 2024, 7, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(75, '2024-08-01', 0.76, 'Agustus\'24', NULL, 2024, 8, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(76, '2024-08-08', 1.01, 'Agustus\'24', NULL, 2024, 8, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(77, '2024-08-15', 1.05, 'Agustus\'24', NULL, 2024, 8, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(78, '2024-08-22', 0.81, 'Agustus\'24', NULL, 2024, 8, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(79, '2024-08-29', 0.35, 'Agustus\'24', NULL, 2024, 8, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(80, '2024-09-01', -2.58, 'September\'24', NULL, 2024, 9, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(81, '2024-09-08', -2.88, 'September\'24', NULL, 2024, 9, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(82, '2024-09-15', -3.05, 'September\'24', NULL, 2024, 9, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(83, '2024-09-22', -3.03, 'September\'24', NULL, 2024, 9, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(84, '2024-10-01', -0.03, 'Oktober\'24', NULL, 2024, 10, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(85, '2024-10-08', -0.1, 'Oktober\'24', NULL, 2024, 10, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(86, '2024-10-15', -0.06, 'Oktober\'24', NULL, 2024, 10, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(87, '2024-10-22', 0.02, 'Oktober\'24', NULL, 2024, 10, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(88, '2024-10-29', 0.19, 'Oktober\'24', NULL, 2024, 10, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(89, '2024-11-01', 0.78, 'November\'24', NULL, 2024, 11, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(90, '2024-11-08', 0.64, 'November\'24', NULL, 2024, 11, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(91, '2024-11-15', 0.7, 'November\'24', NULL, 2024, 11, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(92, '2024-11-22', 0.72, 'November\'24', NULL, 2024, 11, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(93, '2024-12-01', 0.14, 'Desember\'24', NULL, 2024, 12, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(94, '2024-12-08', 0.36, 'Desember\'24', NULL, 2024, 12, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(95, '2024-12-15', 0.71, 'Desember\'24', NULL, 2024, 12, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(96, '2024-12-22', 1.04, 'Desember\'24', NULL, 2024, 12, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(97, '2025-01-01', 3.51, 'Januari\'25', NULL, 2025, 1, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(98, '2025-01-08', 4.26, 'Januari\'25', NULL, 2025, 1, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(99, '2025-01-15', 4.84, 'Januari\'25', NULL, 2025, 1, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(100, '2025-01-22', 4.87, 'Januari\'25', NULL, 2025, 1, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(101, '2025-02-01', -1.04, 'Februari\'25', NULL, 2025, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(102, '2025-02-08', -1.17, 'Februari\'25', NULL, 2025, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(103, '2025-02-15', -1.45, 'Februari\'25', NULL, 2025, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(104, '2025-02-22', -1.14, 'Februari\'25', NULL, 2025, 2, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(105, '2025-03-01', 3.03, 'Maret\'25', NULL, 2025, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(106, '2025-03-08', 2.29, 'Maret\'25', NULL, 2025, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(107, '2025-03-15', 2.28, 'Maret\'25', NULL, 2025, 3, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(108, '2025-04-08', -1.07, 'April\'25', NULL, 2025, 4, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(109, '2025-04-15', -1.31, 'April\'25', NULL, 2025, 4, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(110, '2025-04-22', -2.08, 'April\'25', NULL, 2025, 4, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(111, '2025-05-01', -2.24, 'Mei\'25', NULL, 2025, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(112, '2025-05-15', -2.61, 'Mei\'25', NULL, 2025, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(113, '2025-05-22', -2.81, 'Mei\'25', NULL, 2025, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(114, '2025-05-29', -2.96, 'Mei\'25', NULL, 2025, 5, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(115, '2025-06-01', -1.1, 'Juni\'25', NULL, 2025, 6, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(116, '2025-06-08', -0.86, 'Juni\'25', NULL, 2025, 6, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(117, '2025-06-15', -0.66, 'Juni\'25', NULL, 2025, 6, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28'),
(118, '2025-06-22', -0.43, 'Juni\'25', NULL, 2025, 6, 'BATU', NULL, NULL, NULL, NULL, NULL, NULL, 'uploaded', '2025-10-26 07:01:46', '2025-10-26 07:02:28');

-- --------------------------------------------------------

--
-- Table structure for table `model_performance`
--

CREATE TABLE `model_performance` (
  `id` int NOT NULL,
  `model_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `batch_id` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `mae` float NOT NULL,
  `rmse` float DEFAULT NULL,
  `r2_score` float DEFAULT NULL,
  `cv_score` float DEFAULT NULL,
  `mape` float DEFAULT NULL,
  `training_time` float DEFAULT NULL,
  `data_size` int DEFAULT NULL,
  `test_size` int DEFAULT NULL,
  `is_best` tinyint(1) DEFAULT NULL,
  `feature_importance` text COLLATE utf8mb4_unicode_ci,
  `trained_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `model_performance`
--

INSERT INTO `model_performance` (`id`, `model_name`, `batch_id`, `mae`, `rmse`, `r2_score`, `cv_score`, `mape`, `training_time`, `data_size`, `test_size`, `is_best`, `feature_importance`, `trained_at`, `created_at`) VALUES
(1, 'Random_Forest', 'training_20251026_070155', 0.88015, 1.21999, 0.65378, 0, 52.1298, 0.178439, 91, 19, 0, '[0.2645260835287975, 0.10591037221774596, 0.09697980528763178, 0.10173492788487747, 0.3793409475854776, 0.05150786349546979]', '2025-10-26 07:01:55', '2025-10-26 07:01:55'),
(2, 'XGBoost_Advanced', 'training_20251026_070155', 0.873866, 1.2146, 0.656833, 0, 60.9456, 0.068009, 91, 19, 1, '[0.18624278903007507, 0.08749190717935562, 0.1771370768547058, 0.06978823244571686, 0.4667845666408539, 0.012555381283164024]', '2025-10-26 07:01:55', '2025-10-26 07:01:55'),
(3, 'LightGBM', 'training_20251026_070155', 0.972012, 1.36788, 0.564753, 0, 63.8575, 0.05999, 91, 19, 0, '[305.0, 277.0, 255.0, 256.0, 500.0, 283.0]', '2025-10-26 07:01:55', '2025-10-26 07:01:55'),
(4, 'KNN', 'training_20251026_070155', 0.970398, 1.29608, 0.609243, 0, 57.694, 0, 91, 19, 0, NULL, '2025-10-26 07:01:55', '2025-10-26 07:01:55'),
(5, 'Random_Forest', 'training_20251026_082442', 0.871769, 1.30299, 0.605068, 0, 48.2786, 0.264249, 92, 19, 0, '[0.2647145699296019, 0.10198600192003679, 0.09262059408759118, 0.07467057371673162, 0.4065304484386723, 0.059477811907366174]', '2025-10-26 08:24:43', '2025-10-26 08:24:43'),
(6, 'XGBoost_Advanced', 'training_20251026_082442', 0.666876, 0.965665, 0.783082, 0, 48.6693, 0.032998, 92, 19, 1, '[0.17903946340084076, 0.11325712502002716, 0.15826551616191864, 0.06864909082651138, 0.46546754240989685, 0.01532124262303114]', '2025-10-26 08:24:43', '2025-10-26 08:24:43'),
(7, 'LightGBM', 'training_20251026_082442', 1.02633, 1.50374, 0.474001, 0, 70.2928, 0.023512, 92, 19, 0, '[403.0, 189.0, 262.0, 254.0, 525.0, 314.0]', '2025-10-26 08:24:43', '2025-10-26 08:24:43'),
(8, 'KNN', 'training_20251026_082442', 0.986894, 1.3822, 0.555592, 0, 57.2396, 0, 92, 19, 0, NULL, '2025-10-26 08:24:43', '2025-10-26 08:24:43'),
(9, 'Random_Forest', 'training_20251029_101114', 0.871769, 1.30299, 0.605068, 0, 48.2786, 0.337979, 92, 19, 0, '[0.2647145699296019, 0.10198600192003679, 0.09262059408759118, 0.07467057371673162, 0.4065304484386723, 0.059477811907366174]', '2025-10-29 10:11:15', '2025-10-29 10:11:15'),
(10, 'XGBoost_Advanced', 'training_20251029_101114', 0.666876, 0.965665, 0.783082, 0, 48.6693, 0.042419, 92, 19, 1, '[0.17903946340084076, 0.11325712502002716, 0.15826551616191864, 0.06864909082651138, 0.46546754240989685, 0.01532124262303114]', '2025-10-29 10:11:15', '2025-10-29 10:11:15'),
(11, 'LightGBM', 'training_20251029_101114', 1.02633, 1.50374, 0.474001, 0, 70.2928, 0.034802, 92, 19, 0, '[403.0, 189.0, 262.0, 254.0, 525.0, 314.0]', '2025-10-29 10:11:15', '2025-10-29 10:11:15'),
(12, 'KNN', 'training_20251029_101114', 0.986894, 1.3822, 0.555592, 0, 57.2396, 0, 92, 19, 0, NULL, '2025-10-29 10:11:15', '2025-10-29 10:11:15'),
(13, 'Random_Forest', 'training_20251029_103131', 0.88015, 1.21999, 0.65378, 0, 52.1298, 0.198804, 91, 19, 0, '[0.2645260835287975, 0.10591037221774596, 0.09697980528763178, 0.10173492788487747, 0.3793409475854776, 0.05150786349546979]', '2025-10-29 10:31:32', '2025-10-29 10:31:32'),
(14, 'XGBoost_Advanced', 'training_20251029_103131', 0.873866, 1.2146, 0.656833, 0, 60.9456, 0.038449, 91, 19, 1, '[0.18624278903007507, 0.08749190717935562, 0.1771370768547058, 0.06978823244571686, 0.4667845666408539, 0.012555381283164024]', '2025-10-29 10:31:32', '2025-10-29 10:31:32'),
(15, 'LightGBM', 'training_20251029_103131', 0.972012, 1.36788, 0.564753, 0, 63.8575, 0.026484, 91, 19, 0, '[305.0, 277.0, 255.0, 256.0, 500.0, 283.0]', '2025-10-29 10:31:32', '2025-10-29 10:31:32'),
(16, 'KNN', 'training_20251029_103131', 0.970398, 1.29608, 0.609243, 0, 57.694, 0.0021, 91, 19, 0, NULL, '2025-10-29 10:31:32', '2025-10-29 10:31:32');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `ix_activity_logs_entity_type` (`entity_type`),
  ADD KEY `ix_activity_logs_created_at` (`created_at`),
  ADD KEY `ix_activity_logs_action_type` (`action_type`);

--
-- Indexes for table `admin_users`
--
ALTER TABLE `admin_users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `alert_history`
--
ALTER TABLE `alert_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_alert_created` (`created_at`),
  ADD KEY `ix_alert_history_severity` (`severity`),
  ADD KEY `ix_alert_history_alert_type` (`alert_type`),
  ADD KEY `idx_alert_active` (`is_active`),
  ADD KEY `idx_alert_type_severity` (`alert_type`,`severity`),
  ADD KEY `ix_alert_history_created_at` (`created_at`);

--
-- Indexes for table `alert_rules`
--
ALTER TABLE `alert_rules`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `rule_name` (`rule_name`);

--
-- Indexes for table `commodity_data`
--
ALTER TABLE `commodity_data`
  ADD PRIMARY KEY (`id`),
  ADD KEY `iph_id` (`iph_id`),
  ADD KEY `ix_commodity_data_tanggal` (`tanggal`),
  ADD KEY `ix_commodity_data_tahun` (`tahun`),
  ADD KEY `idx_commodity_minggu` (`minggu`),
  ADD KEY `idx_commodity_date_bulan` (`tanggal`,`bulan`),
  ADD KEY `ix_commodity_data_minggu` (`minggu`),
  ADD KEY `ix_commodity_data_bulan` (`bulan`),
  ADD KEY `idx_commodity_tahun_bulan` (`tahun`,`bulan`);

--
-- Indexes for table `forecast_history`
--
ALTER TABLE `forecast_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_forecast_history_created_at` (`created_at`),
  ADD KEY `idx_forecast_model_date` (`model_name`,`created_at`),
  ADD KEY `ix_forecast_history_model_name` (`model_name`),
  ADD KEY `idx_forecast_created` (`created_at`);

--
-- Indexes for table `iph_data`
--
ALTER TABLE `iph_data`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_iph_data_tanggal` (`tanggal`),
  ADD KEY `ix_iph_data_tahun` (`tahun`),
  ADD KEY `ix_iph_data_bulan` (`bulan`),
  ADD KEY `ix_iph_data_minggu` (`minggu`);

--
-- Indexes for table `model_performance`
--
ALTER TABLE `model_performance`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_best_models` (`is_best`,`mae`),
  ADD KEY `ix_model_performance_trained_at` (`trained_at`),
  ADD KEY `idx_model_performance` (`model_name`,`trained_at`),
  ADD KEY `ix_model_performance_model_name` (`model_name`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `activity_logs`
--
ALTER TABLE `activity_logs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `admin_users`
--
ALTER TABLE `admin_users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `alert_history`
--
ALTER TABLE `alert_history`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `alert_rules`
--
ALTER TABLE `alert_rules`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `commodity_data`
--
ALTER TABLE `commodity_data`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=119;

--
-- AUTO_INCREMENT for table `forecast_history`
--
ALTER TABLE `forecast_history`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `iph_data`
--
ALTER TABLE `iph_data`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=119;

--
-- AUTO_INCREMENT for table `model_performance`
--
ALTER TABLE `model_performance`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD CONSTRAINT `activity_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `admin_users` (`id`);

--
-- Constraints for table `commodity_data`
--
ALTER TABLE `commodity_data`
  ADD CONSTRAINT `commodity_data_ibfk_1` FOREIGN KEY (`iph_id`) REFERENCES `iph_data` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
