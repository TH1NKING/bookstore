-- Sample categories
INSERT INTO categories (name, description) VALUES
  ('Fiction', 'Fictional works'),
  ('Science', 'Scientific books'),
  ('History', 'Historical books'),
  ('Business', 'Business related titles'),
  ('Children', 'Books for children');

-- Sample books
INSERT INTO books (title, author, publisher, publish_date, price, stock, category_id, description, cover_image, created_at)
VALUES
  ('The Great Gatsby', 'F. Scott Fitzgerald', 'Scribner', '1925-04-10', 10.99, 15, 1, 'Classic novel set in the Jazz Age', NULL, NOW()),
  ('To Kill a Mockingbird', 'Harper Lee', 'J.B. Lippincott & Co.', '1960-07-11', 7.99, 10, 1, 'Story of racial injustice in the Deep South', NULL, NOW()),
  ('1984', 'George Orwell', 'Secker & Warburg', '1949-06-08', 8.99, 12, 1, 'Dystopian social science fiction novel', NULL, NOW()),
  ('A Brief History of Time', 'Stephen Hawking', 'Bantam Books', '1988-04-01', 12.50, 8, 2, 'Cosmology for the general reader', NULL, NOW()),
  ('The Selfish Gene', 'Richard Dawkins', 'Oxford University Press', '1976-05-01', 9.75, 5, 2, 'Evolutionary biology classic', NULL, NOW()),
  ('Sapiens', 'Yuval Noah Harari', 'Harper', '2011-01-01', 14.00, 7, 3, 'History of humankind', NULL, NOW()),
  ('Guns, Germs, and Steel', 'Jared Diamond', 'W. W. Norton & Company', '1997-03-01', 13.50, 6, 3, 'Exploration of societal development', NULL, NOW()),
  ('The Lean Startup', 'Eric Ries', 'Crown Business', '2011-09-13', 16.00, 9, 4, 'Entrepreneurship guide', NULL, NOW()),
  ('Good to Great', 'Jim Collins', 'HarperBusiness', '2001-10-16', 15.00, 4, 4, 'Business management study', NULL, NOW()),
  ('Green Eggs and Ham', 'Dr. Seuss', 'Random House', '1960-08-12', 6.50, 20, 5, 'Children''s rhyming story', NULL, NOW()),
  ('Charlotte''s Web', 'E. B. White', 'Harper & Brothers', '1952-10-15', 7.00, 18, 5, 'Friendship of a pig and a spider', NULL, NOW()),
  ('The Cat in the Hat', 'Dr. Seuss', 'Random House', '1957-03-12', 6.75, 22, 5, 'Cat brings mischief to two children', NULL, NOW()),
  ('The Hobbit', 'J.R.R. Tolkien', 'George Allen & Unwin', '1937-09-21', 11.99, 11, 1, 'Fantasy adventure prelude to Lord of the Rings', NULL, NOW()),
  ('Freakonomics', 'Steven Levitt and Stephen Dubner', 'William Morrow', '2005-04-12', 14.95, 8, 4, 'Unconventional economic insights', NULL, NOW()),
  ('The Wright Brothers', 'David McCullough', 'Simon & Schuster', '2015-05-05', 13.25, 7, 3, 'Biography of aviation pioneers', NULL, NOW()),
  ('Thinking, Fast and Slow', 'Daniel Kahneman', 'Farrar, Straus and Giroux', '2011-10-25', 12.75, 9, 4, 'Insights into human decision making', NULL, NOW()),
  ('The Martian', 'Andy Weir', 'Crown Publishing', '2011-02-11', 10.50, 14, 1, 'Astronaut stranded on Mars', NULL, NOW()),
  ('The Immortal Life of Henrietta Lacks', 'Rebecca Skloot', 'Crown Publishing', '2010-02-02', 12.00, 6, 3, 'Story behind the HeLa cells', NULL, NOW()),
  ('Harry Potter and the Sorcerer''s Stone', 'J.K. Rowling', 'Bloomsbury', '1997-06-26', 9.99, 30, 1, 'First book of Harry Potter series', NULL, NOW()),
  ('The Diary of a Young Girl', 'Anne Frank', 'Contact Publishing', '1947-06-25', 8.50, 10, 3, 'Diary of Anne Frank during WWII', NULL, NOW());
