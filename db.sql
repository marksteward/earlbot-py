CREATE TABLE uri (
    uri string, nick string, channel string, timestamp int,
    PRIMARY KEY(uri, channel)
);
