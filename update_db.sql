-- 添加私有字段
ALTER TABLE website ADD COLUMN is_private BOOLEAN DEFAULT 0;
-- 添加可见用户字段
ALTER TABLE website ADD COLUMN visible_to TEXT DEFAULT ''; 