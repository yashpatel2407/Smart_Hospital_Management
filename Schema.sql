-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Feb 19, 2026 at 04:10 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `smartcare_hospital`
--

-- --------------------------------------------------------

--
-- Table structure for table `appointments`
--

CREATE TABLE `appointments` (
  `id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `doctor_id` int(11) NOT NULL,
  `appointment_date` date NOT NULL,
  `appointment_time` time NOT NULL,
  `status` enum('pending','confirmed','completed','cancelled') DEFAULT 'pending',
  `reason` text DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `appointments`
--

INSERT INTO `appointments` (`id`, `patient_id`, `doctor_id`, `appointment_date`, `appointment_time`, `status`, `reason`, `notes`, `created_at`, `updated_at`) VALUES
(1, 1, 2, '2026-02-19', '15:40:00', 'completed', 'Check-up', NULL, '2026-02-19 10:06:56', '2026-02-19 12:53:46'),
(2, 1, 2, '2026-02-19', '16:40:00', 'cancelled', 'CheckUP,visit', NULL, '2026-02-19 10:21:45', '2026-02-19 10:22:14');

-- --------------------------------------------------------

--
-- Table structure for table `bills`
--

CREATE TABLE `bills` (
  `id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `appointment_id` int(11) DEFAULT NULL,
  `total_amount` decimal(10,2) NOT NULL DEFAULT 0.00,
  `discount` decimal(10,2) DEFAULT 0.00,
  `tax` decimal(10,2) DEFAULT 0.00,
  `net_amount` decimal(10,2) NOT NULL DEFAULT 0.00,
  `payment_status` enum('unpaid','paid','partial') DEFAULT 'unpaid',
  `payment_method` enum('cash','card','upi','insurance') DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bills`
--

INSERT INTO `bills` (`id`, `patient_id`, `appointment_id`, `total_amount`, `discount`, `tax`, `net_amount`, `payment_status`, `payment_method`, `created_at`, `updated_at`) VALUES
(1, 1, 1, 580.00, 0.00, 0.00, 580.00, 'paid', 'upi', '2026-02-19 12:53:46', '2026-02-19 13:42:14');

-- --------------------------------------------------------

--
-- Table structure for table `bill_items`
--

CREATE TABLE `bill_items` (
  `id` int(11) NOT NULL,
  `bill_id` int(11) NOT NULL,
  `description` varchar(255) NOT NULL,
  `item_type` enum('consultation','medicine','lab_test','procedure','other') DEFAULT 'other',
  `quantity` int(11) NOT NULL DEFAULT 1,
  `unit_price` decimal(10,2) NOT NULL DEFAULT 0.00,
  `total_price` decimal(10,2) NOT NULL DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bill_items`
--

INSERT INTO `bill_items` (`id`, `bill_id`, `description`, `item_type`, `quantity`, `unit_price`, `total_price`) VALUES
(1, 1, 'Doctor Consultation Fee', 'consultation', 1, 500.00, 500.00),
(2, 1, 'Medicine: Metformin 500mg', 'medicine', 2, 40.00, 80.00);

-- --------------------------------------------------------

--
-- Table structure for table `doctors`
--

CREATE TABLE `doctors` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `specialization` varchar(100) NOT NULL,
  `qualification` varchar(200) NOT NULL,
  `experience_years` int(11) DEFAULT 0,
  `consultation_fee` decimal(10,2) DEFAULT 0.00,
  `available_days` varchar(100) DEFAULT 'Mon,Tue,Wed,Thu,Fri',
  `available_time_start` time DEFAULT '09:00:00',
  `available_time_end` time DEFAULT '17:00:00',
  `bio` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `doctors`
--

INSERT INTO `doctors` (`id`, `user_id`, `specialization`, `qualification`, `experience_years`, `consultation_fee`, `available_days`, `available_time_start`, `available_time_end`, `bio`, `created_at`) VALUES
(2, 3, 'Cardiology', 'MBBS', 5, 500.00, 'Mon,Tue,Wed,Thu,Fri', '09:00:00', '17:00:00', NULL, '2026-02-19 09:29:16'),
(3, 5, 'Cardiology', 'MBBS, MD', 10, 600.00, 'Mon,Tue,Wed,Thu,Fri', '09:00:00', '17:00:00', NULL, '2026-02-19 13:32:36'),
(4, 6, 'Neurology', 'MBBS', 7, 450.00, 'Mon,Tue,Wed,Thu,Fri', '09:00:00', '17:00:00', NULL, '2026-02-19 13:33:37'),
(5, 7, 'Pediatrics', 'MBBS', 5, 400.00, 'Mon,Tue,Wed,Thu,Fri', '09:00:00', '17:00:00', NULL, '2026-02-19 13:34:41'),
(6, 8, 'Orthopedics', 'MBBS, MD, DM', 8, 500.00, 'Mon,Tue,Wed,Thu,Fri', '09:00:00', '17:00:00', NULL, '2026-02-19 13:35:52');

-- --------------------------------------------------------

--
-- Table structure for table `doctor_unavailability`
--

CREATE TABLE `doctor_unavailability` (
  `id` int(11) NOT NULL,
  `doctor_id` int(11) NOT NULL,
  `unavailable_date` date NOT NULL,
  `reason` varchar(255) DEFAULT NULL,
  `status` enum('pending','approved','rejected') DEFAULT 'pending',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `doctor_unavailability`
--

INSERT INTO `doctor_unavailability` (`id`, `doctor_id`, `unavailable_date`, `reason`, `created_at`) VALUES
(1, 2, '2026-02-23', 'Personal Reasons', '2026-02-19 13:38:19');

-- --------------------------------------------------------

--
-- Table structure for table `medical_reports`
--

CREATE TABLE `medical_reports` (
  `id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `doctor_id` int(11) DEFAULT NULL,
  `report_type` varchar(100) NOT NULL,
  `report_title` varchar(255) NOT NULL,
  `file_path` varchar(500) DEFAULT NULL,
  `findings` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `medical_reports`
--

INSERT INTO `medical_reports` (`id`, `patient_id`, `doctor_id`, `report_type`, `report_title`, `file_path`, `findings`, `created_at`) VALUES
(1, 1, NULL, 'X-Ray', 'Yash_XRay', 'uploads/report_1_xray.jpg', '', '2026-02-19 10:26:01');

-- --------------------------------------------------------

--
-- Table structure for table `medicines`
--

CREATE TABLE `medicines` (
  `id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `manufacturer` varchar(200) DEFAULT NULL,
  `price` decimal(10,2) NOT NULL DEFAULT 0.00,
  `stock_quantity` int(11) NOT NULL DEFAULT 0,
  `expiry_date` date DEFAULT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `medicines`
--

INSERT INTO `medicines` (`id`, `name`, `category`, `manufacturer`, `price`, `stock_quantity`, `expiry_date`, `description`, `created_at`, `updated_at`) VALUES
(1, 'Paracetamol 500mg', 'Tablet', 'Cipla', 25.00, 200, '2027-06-15', 'Pain reliever and fever reducer', '2026-02-19 09:19:39', '2026-02-19 09:19:39'),
(2, 'Amoxicillin 250mg', 'Capsule', 'Sun Pharma', 85.00, 150, '2027-03-20', 'Antibiotic for bacterial infections', '2026-02-19 09:19:39', '2026-02-19 09:19:39'),
(3, 'Cetirizine 10mg', 'Tablet', 'Dr Reddy', 35.00, 300, '2027-09-10', 'Antihistamine for allergies', '2026-02-19 09:19:39', '2026-02-19 09:19:39'),
(4, 'Omeprazole 20mg', 'Capsule', 'Ranbaxy', 55.00, 180, '2027-04-25', 'Proton pump inhibitor for acid reflux', '2026-02-19 09:19:39', '2026-02-19 09:19:39'),
(5, 'Metformin 500mg', 'Tablet', 'USV', 40.00, 250, '2027-08-30', 'Diabetes management', '2026-02-19 09:19:39', '2026-02-19 09:19:39'),
(6, 'Ibuprofen 400mg', 'Tablet', 'Cipla', 30.00, 220, '2027-07-12', 'Anti-inflammatory pain reliever', '2026-02-19 09:19:39', '2026-02-19 09:19:39'),
(7, 'Azithromycin 500mg', 'Tablet', 'Zydus', 120.00, 100, '2027-05-18', 'Antibiotic (macrolide)', '2026-02-19 09:19:39', '2026-02-19 09:19:39'),
(8, 'Pantoprazole 40mg', 'Tablet', 'Sun Pharma', 65.00, 160, '2027-11-05', 'Gastric acid reducer', '2026-02-19 09:19:39', '2026-02-19 09:19:39'),
(9, 'Dolo 650mg', 'Tablet', 'Micro Labs', 28.00, 350, '2027-12-01', 'Fever and pain relief', '2026-02-19 09:19:39', '2026-02-19 09:19:39'),
(10, 'Vitamin D3 60K', 'Capsule', 'USV', 45.00, 90, '2027-10-20', 'Vitamin D supplement', '2026-02-19 09:19:39', '2026-02-19 09:19:39');

-- --------------------------------------------------------

--
-- Table structure for table `patients`
--

CREATE TABLE `patients` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `blood_group` enum('A+','A-','B+','B-','AB+','AB-','O+','O-') DEFAULT NULL,
  `emergency_contact` varchar(15) DEFAULT NULL,
  `medical_history` text DEFAULT NULL,
  `allergies` text DEFAULT NULL,
  `insurance_id` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `patients`
--

INSERT INTO `patients` (`id`, `user_id`, `blood_group`, `emergency_contact`, `medical_history`, `allergies`, `insurance_id`, `created_at`) VALUES
(1, 4, 'O+', NULL, NULL, NULL, NULL, '2026-02-19 09:43:59');

-- --------------------------------------------------------

--
-- Table structure for table `prescriptions`
--

CREATE TABLE `prescriptions` (
  `id` int(11) NOT NULL,
  `appointment_id` int(11) NOT NULL,
  `doctor_id` int(11) NOT NULL,
  `patient_id` int(11) NOT NULL,
  `diagnosis` text NOT NULL,
  `notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `prescriptions`
--

INSERT INTO `prescriptions` (`id`, `appointment_id`, `doctor_id`, `patient_id`, `diagnosis`, `notes`, `created_at`) VALUES
(1, 1, 2, 1, 'Acute Myocardial Infarction (Heart Attack)', 'Patient presents with severe chest pain radiating to left arm, sweating, shortness of breath, and nausea. ECG shows ST-segment elevation. Troponin levels elevated. Blood pressure 150/95 mmHg. History of hypertension and smoking.', '2026-02-19 12:53:46');

-- --------------------------------------------------------

--
-- Table structure for table `prescription_medicines`
--

CREATE TABLE `prescription_medicines` (
  `id` int(11) NOT NULL,
  `prescription_id` int(11) NOT NULL,
  `medicine_name` varchar(200) NOT NULL,
  `dosage` varchar(100) NOT NULL,
  `frequency` varchar(100) NOT NULL,
  `duration` varchar(100) NOT NULL,
  `instructions` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `prescription_medicines`
--

INSERT INTO `prescription_medicines` (`id`, `prescription_id`, `medicine_name`, `dosage`, `frequency`, `duration`, `instructions`) VALUES
(1, 1, 'Metformin 500mg', '500mg', '1-0-1', '3', '');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(120) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `password_hash` varchar(256) NOT NULL,
  `role` enum('admin','doctor','patient') NOT NULL DEFAULT 'patient',
  `gender` enum('male','female','other') DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `address` text DEFAULT NULL,
  `profile_image` varchar(256) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `full_name`, `email`, `phone`, `password_hash`, `role`, `gender`, `date_of_birth`, `address`, `profile_image`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'Admin User', 'admin@smartcare.com', '9999999999', 'scrypt:32768:8:1$s46nwveTpGYWUmWt$999dabf350bdcdd2e2c1ddacd8c1968dfcebef95c9409c72ce8e62f1f3527878954447bce1c81ad6c8d60191b4da9045ea1747e9a39126077e4f5c2c803b3bb4', 'admin', NULL, NULL, NULL, NULL, 1, '2026-02-19 09:20:41', '2026-02-19 09:20:41'),
(3, 'Smit', 'smitgondaliya12@gmail.com', '9723389779', 'scrypt:32768:8:1$sqvaVUAxymYUoHbT$a43b825bbafcda86d2d19c7ac60d0480b796cf77523228757d6ca41c66d7b8ca16637a189d35ed990b3b3dbd198858c8c1ac295a4e0da1ae8e605fbfb4c20d94', 'doctor', NULL, NULL, NULL, NULL, 1, '2026-02-19 09:29:16', '2026-02-19 09:29:16'),
(4, 'Yash Patel', 'yashpatel24727@gmail.com', '7016986613', 'scrypt:32768:8:1$oExt9ZzVAXHApkBI$d8f755be2d97279ff6ccf37e5874655f69741e8fb76b4e210d4ddb97b76a7cefbb23ebd9fb9757d18180811f6507d6b0997ad94f29af5e1c58ad38e56324a861', 'patient', 'male', '2007-07-24', NULL, NULL, 1, '2026-02-19 09:43:59', '2026-02-19 09:43:59'),
(5, 'Naresh Trehan', 'nareshtrehan@gmail.com', '9876543210', 'scrypt:32768:8:1$cVE43OqtSpO6iOHl$716dd36785b063c8a9ec764dee2f42e958358a7cdf137f0a47929350f577daa9f5b83b2ae03087f06b1a74136debd03d6d9fa0bc71d40a201395996b4e3a1b74', 'doctor', NULL, NULL, NULL, NULL, 1, '2026-02-19 13:32:36', '2026-02-19 13:32:36'),
(6, 'Robert Chen', 'robertchen@gmail.com', '9876543210', 'scrypt:32768:8:1$xPjqlM3s6rCoIBcw$d70014274e34a455ec2d04bb5b7dba9ded9fbf07418bffa6da815f745faeda915e2fc112910c8465a9a61fc47c51fa2c694b0516a32d2908904db1859cdaa39d', 'doctor', NULL, NULL, NULL, NULL, 1, '2026-02-19 13:33:37', '2026-02-19 13:33:37'),
(7, 'Emily Watts', 'emilywatts@gmail.com', '9876543210', 'scrypt:32768:8:1$tBvshHruxQFVMJYv$1bb16911e92df053d2eee23fde6cb03a16182bd0084c84139c7b91e58008baa5651f990a75d500ef82e8f6fb7ed78f379330ea758011ea0ff217caeb0f66a40a', 'doctor', NULL, NULL, NULL, NULL, 1, '2026-02-19 13:34:41', '2026-02-19 13:34:41'),
(8, 'James Wilson', 'jameswilson@gmail.com', '9876543210', 'scrypt:32768:8:1$JoZcUqwTYRxtgio5$23aa048f17bf1075b9bdffdc85b4593fe1582bf57bac38ffd94a2593fa62c146354e56b09cf95cf185786b44aef96f90a2a167a4253f143922394b835693c95b', 'doctor', NULL, NULL, NULL, NULL, 1, '2026-02-19 13:35:52', '2026-02-19 13:35:52');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `appointments`
--
ALTER TABLE `appointments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `patient_id` (`patient_id`),
  ADD KEY `doctor_id` (`doctor_id`);

--
-- Indexes for table `bills`
--
ALTER TABLE `bills`
  ADD PRIMARY KEY (`id`),
  ADD KEY `patient_id` (`patient_id`),
  ADD KEY `appointment_id` (`appointment_id`);

--
-- Indexes for table `bill_items`
--
ALTER TABLE `bill_items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `bill_id` (`bill_id`);

--
-- Indexes for table `doctors`
--
ALTER TABLE `doctors`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- Indexes for table `doctor_unavailability`
--
ALTER TABLE `doctor_unavailability`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `doctor_id` (`doctor_id`,`unavailable_date`);

--
-- Indexes for table `medical_reports`
--
ALTER TABLE `medical_reports`
  ADD PRIMARY KEY (`id`),
  ADD KEY `patient_id` (`patient_id`),
  ADD KEY `doctor_id` (`doctor_id`);

--
-- Indexes for table `medicines`
--
ALTER TABLE `medicines`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `patients`
--
ALTER TABLE `patients`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- Indexes for table `prescriptions`
--
ALTER TABLE `prescriptions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `appointment_id` (`appointment_id`),
  ADD KEY `doctor_id` (`doctor_id`),
  ADD KEY `patient_id` (`patient_id`);

--
-- Indexes for table `prescription_medicines`
--
ALTER TABLE `prescription_medicines`
  ADD PRIMARY KEY (`id`),
  ADD KEY `prescription_id` (`prescription_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `appointments`
--
ALTER TABLE `appointments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `bills`
--
ALTER TABLE `bills`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `bill_items`
--
ALTER TABLE `bill_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `doctors`
--
ALTER TABLE `doctors`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `doctor_unavailability`
--
ALTER TABLE `doctor_unavailability`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `medical_reports`
--
ALTER TABLE `medical_reports`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `medicines`
--
ALTER TABLE `medicines`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `patients`
--
ALTER TABLE `patients`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `prescriptions`
--
ALTER TABLE `prescriptions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `prescription_medicines`
--
ALTER TABLE `prescription_medicines`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `appointments`
--
ALTER TABLE `appointments`
  ADD CONSTRAINT `appointments_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `appointments_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `bills`
--
ALTER TABLE `bills`
  ADD CONSTRAINT `bills_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `bills_ibfk_2` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `bill_items`
--
ALTER TABLE `bill_items`
  ADD CONSTRAINT `bill_items_ibfk_1` FOREIGN KEY (`bill_id`) REFERENCES `bills` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `doctors`
--
ALTER TABLE `doctors`
  ADD CONSTRAINT `doctors_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `doctor_unavailability`
--
ALTER TABLE `doctor_unavailability`
  ADD CONSTRAINT `doctor_unavailability_ibfk_1` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `medical_reports`
--
ALTER TABLE `medical_reports`
  ADD CONSTRAINT `medical_reports_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `medical_reports_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `patients`
--
ALTER TABLE `patients`
  ADD CONSTRAINT `patients_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `prescriptions`
--
ALTER TABLE `prescriptions`
  ADD CONSTRAINT `prescriptions_ibfk_1` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `prescriptions_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `prescriptions_ibfk_3` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `prescription_medicines`
--
ALTER TABLE `prescription_medicines`
  ADD CONSTRAINT `prescription_medicines_ibfk_1` FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
