"""
File:           models.py
Author:         Dibyaranjan Sathua
Created on:     19/12/2020, 18:17
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.Text)
    genres = db.relationship('VenuesGenres', backref='venue', lazy=True)
    shows = db.relationship('Show', backref='venue', lazy=True)

    @property
    def upcoming_shows(self):
        """ Return list of upcoming shows for the venue """
        now = datetime.now()
        # all_show = Show.query.filter_by(venue_id=self.id).all()
        # upcoming_shows = [x for x in all_show if x.start_time >= now]
        # Join reference
        # https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_orm_working_with_joins.htm
        upcoming_shows = Show.query.join(Venue).filter(Show.start_time >= now).all()
        return upcoming_shows

    @property
    def past_shows(self):
        """ Return list of past shows for the venue """
        now = datetime.now()
        # all_show = Show.query.filter_by(venue_id=self.id).all()
        # past_shows = [x for x in all_show if x.start_time < now]
        past_shows = Show.query.join(Venue).filter(Show.start_time < now).all()
        return past_shows

    @property
    def genres_list(self):
        """ Return list of venue genres """
        # genres = VenuesGenres.query.filter_by(venue_id=self.id).all()
        return [x.genre for x in self.genres]


class VenuesGenres(db.Model):
    __tablename__ = 'VenuesGenres'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    genre = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return f'{self.__class__.__name__} [{self.id}, {self.genre}]'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.Text)
    genres = db.relationship('ArtistsGenres', backref='artist', lazy=True)
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f'{self.__class__.__name__} [{self.id}, {self.name}]'

    def __str__(self):
        return self.__repr__()

    @property
    def upcoming_shows(self):
        """ Return list of upcoming shows for the venue """
        now = datetime.now()
        # all_show = Show.query.filter_by(artist_id=self.id).all()
        # upcoming_shows = [x for x in all_show if x.start_time >= now]
        upcoming_shows = Show.query.join(Artist).filter(Show.start_time >= now).all()
        return upcoming_shows

    @property
    def past_shows(self):
        """ Return list of past shows for the venue """
        now = datetime.now()
        # all_show = Show.query.filter_by(artist_id=self.id).all()
        # past_shows = [x for x in all_show if x.start_time < now]
        past_shows = Show.query.join(Artist).filter(Show.start_time < now).all()
        return past_shows

    @property
    def genres_list(self):
        """ Return list of venue genres """
        # genres = ArtistsGenres.query.filter_by(artist_id=self.id).all()
        return [x.genre for x in self.genres]


class ArtistsGenres(db.Model):
    __tablename__ = 'ArtistsGenres'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    genre = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return f'{self.__class__.__name__} [{self.id}, {self.genre}]'


class Show(db.Model):
    __tablename__ = 'Shows'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'{self.__class__.__name__} [{self.id}, {self.venue_id}, {self.artist_id}]'

    def __str__(self):
        return self.__repr__()
