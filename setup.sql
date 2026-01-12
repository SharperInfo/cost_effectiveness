CREATE TABLE messages (
    sender text NOT NULL,
    recipient text NOT NULL,
    message text NOT NULL
);

INSERT INTO messages (sender, recipient, message) VALUES (
    'Craig', 'Jenn', 'Hello!'
);
