CREATE TABLE IF NOT EXISTS tbl_user (
    user_sn INT AUTO_INCREMENT PRIMARY KEY,
    employee_no VARCHAR(40) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'USER',
    password_hash VARCHAR(255) NOT NULL,
    first_login TINYINT(1) NOT NULL DEFAULT 1,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    crt_dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mdfcn_dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tbl_project (
    prj_sn INT AUTO_INCREMENT PRIMARY KEY,
    prj_nm VARCHAR(200) NOT NULL,
    crt_dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO tbl_project (prj_sn, prj_nm)
VALUES (1, 'First Project');

CREATE TABLE IF NOT EXISTS tbl_file (
    file_sn INT AUTO_INCREMENT PRIMARY KEY,
    prj_sn INT NOT NULL DEFAULT 1,
    file_cd VARCHAR(30) NOT NULL,
    file_nm VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL DEFAULT 0,
    file_ext VARCHAR(20) NULL,
    doc_state VARCHAR(30) NOT NULL DEFAULT '등록완료',
    del_yn CHAR(1) NOT NULL DEFAULT 'N',
    crt_dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creatr_sn INT NULL,
    mdfcn_dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    mdfr_sn INT NULL,
    INDEX idx_tbl_file_project (prj_sn, del_yn),
    CONSTRAINT fk_tbl_file_project
        FOREIGN KEY (prj_sn) REFERENCES tbl_project (prj_sn)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tbl_docs (
    docs_sn INT AUTO_INCREMENT PRIMARY KEY,
    prj_sn INT NOT NULL DEFAULT 1,
    pssn_user_sn INT NULL,
    docs_cd VARCHAR(30) NOT NULL,
    docs_ver VARCHAR(30) NOT NULL DEFAULT 'v1.0',
    mdfcn_cn TEXT NULL,
    crt_dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creatr_sn INT NULL,
    mdfcn_dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    mdfr_sn INT NULL,
    INDEX idx_tbl_docs_project (prj_sn, docs_cd),
    CONSTRAINT fk_tbl_docs_project
        FOREIGN KEY (prj_sn) REFERENCES tbl_project (prj_sn)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tbl_docs_detail (
    docs_dtl_sn INT AUTO_INCREMENT PRIMARY KEY,
    docs_sn INT NOT NULL,
    docs_path TEXT NOT NULL,
    del_yn CHAR(1) NOT NULL DEFAULT 'N',
    crt_dt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creatr_sn INT NULL,
    INDEX idx_tbl_docs_detail_docs (docs_sn, del_yn),
    CONSTRAINT fk_tbl_docs_detail_docs
        FOREIGN KEY (docs_sn) REFERENCES tbl_docs (docs_sn)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
