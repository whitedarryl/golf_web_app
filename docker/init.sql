-- Golf Web App Database Initialization for Docker
-- This script runs automatically when the MySQL container first starts

-- =============================================================================
-- Courses table: Stores information about golf courses and tournaments
-- =============================================================================
CREATE TABLE IF NOT EXISTS courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(255) NOT NULL,
    tournament_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_courses_name_date (course_name, tournament_date),
    INDEX idx_courses_date (tournament_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- Players table: Stores player roster for each tournament
-- =============================================================================
CREATE TABLE IF NOT EXISTS players (
    player_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    course_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    INDEX idx_players_course (course_id),
    INDEX idx_players_name (first_name(50), last_name(50)),
    INDEX idx_players_course_name (course_id, first_name(50), last_name(50))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- Scores table: Stores individual hole scores and calculated totals
-- =============================================================================
CREATE TABLE IF NOT EXISTS scores (
    score_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    course_id INT,
    hole_1 INT,
    hole_2 INT,
    hole_3 INT,
    hole_4 INT,
    hole_5 INT,
    hole_6 INT,
    hole_7 INT,
    hole_8 INT,
    hole_9 INT,
    hole_10 INT,
    hole_11 INT,
    hole_12 INT,
    hole_13 INT,
    hole_14 INT,
    hole_15 INT,
    hole_16 INT,
    hole_17 INT,
    hole_18 INT,
    total INT,
    net_score INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    INDEX idx_scores_course_player (course_id, first_name(50), last_name(50)),
    INDEX idx_scores_total (total),
    INDEX idx_scores_net (net_score),
    INDEX idx_scores_course_total (course_id, total),
    INDEX idx_scores_course_net (course_id, net_score),
    INDEX idx_scores_submitted (course_id, total)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- Course hole handicap table: Stores handicap rankings for each hole
-- =============================================================================
CREATE TABLE IF NOT EXISTS course_hole_handicap (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    hole_number INT NOT NULL,
    handicap_rank INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE KEY unique_course_hole (course_id, hole_number),
    INDEX idx_course_hole_course (course_id),
    INDEX idx_course_hole_rank (course_id, handicap_rank)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- Scores archive table: Historical storage of completed tournaments
-- =============================================================================
CREATE TABLE IF NOT EXISTS scores_archive (
    archive_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    course_name VARCHAR(255),
    date_played DATE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    total INT,
    net_score INT,
    snapshot_id INT,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_archive_course (course_id),
    INDEX idx_archive_date (date_played),
    INDEX idx_archive_course_date (course_name(50), date_played),
    INDEX idx_archive_player (first_name(50), last_name(50))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- Fives table: Stores "Five Five Five" tournament specific data
-- =============================================================================
CREATE TABLE IF NOT EXISTS fives (
    five_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    juniors INT DEFAULT 0,
    seniors_ladies INT DEFAULT 0,
    handicap DECIMAL(10,2),
    front_9 INT,
    front_9_net DECIMAL(10,2),
    back_9 INT,
    back_9_net DECIMAL(10,2),
    total INT,
    total_net DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    INDEX idx_fives_course (course_id),
    INDEX idx_fives_player (first_name(50), last_name(50))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- Create a default course entry
-- =============================================================================
INSERT INTO courses (course_id, course_name, tournament_date)
VALUES (1, 'Default Course', CURDATE())
ON DUPLICATE KEY UPDATE course_name=course_name;
