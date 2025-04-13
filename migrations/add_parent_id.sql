-- 添加parent_id字段到category表中
ALTER TABLE category ADD COLUMN parent_id INTEGER;

-- 添加外键约束
ALTER TABLE category ADD CONSTRAINT fk_category_parent 
    FOREIGN KEY (parent_id) REFERENCES category(id); 