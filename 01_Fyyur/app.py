#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from models import Venue, VenuesGenres, Artist, ArtistsGenres, Show, db
from forms import ShowForm, VenueForm, ArtistForm
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
# Add Csrf protect for {'csrf_token': ['The CSRF token is missing.']} error on form submission
csrf = CSRFProtect(app=app)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = " EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    """ Get all venues """
    data = []
    all_venues = Venue.query.all()
    unique_locations = set([(x.city, x.state) for x in all_venues])
    for location in unique_locations:
        venues = [
            {
                'id': x.id,
                'name': x.name,
                'num_upcoming_shows': len(x.upcoming_shows)
            }
            for x in all_venues if x.city == location[0] and x.state == location[1]
        ]
        data.append(
            {
                'city': location[0],
                'state': location[1],
                'venues': venues
            }
        )

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    """ Search for a venue using search_term """
    search_term = request.form.get('search_term')
    # Reference: https://stackoverflow.com/questions/3325467/sqlalchemy-equivalent-to-sql-like-statement
    # Get all venues using LIKE sql statement
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    data = [
        {
            'id': x.id,
            'name': x.name,
            'num_upcoming_shows': len(x.upcoming_shows)
        }
        for x in venues
    ]
    response = {
        'count': len(data),
        'data': data
    }
    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=request.form.get('search_term', '')
    )


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    """ Show a venue by id """
    venue = Venue.query.get(venue_id)
    # Upcoming show details
    upcoming_shows_details = [
        {
            'artist_id': x.artist_id,
            'artist_name': x.artist.name,
            'artist_image_link': x.artist.image_link,
            'start_time': x.start_time.isoformat()
        }
        for x in venue.upcoming_shows
    ]

    # Past show details
    past_show_details = [
        {
            'artist_id': x.artist_id,
            'artist_name': x.artist.name,
            'artist_image_link': x.artist.image_link,
            'start_time': x.start_time.isoformat()
        }
        for x in venue.past_shows
    ]

    data = {
        'id': venue_id,
        'name': venue.name,
        'genres': venue.genres_list,
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'past_shows': past_show_details,
        'upcoming_shows': upcoming_shows_details,
        'past_shows_count': len(past_show_details),
        'upcoming_shows_count': len(upcoming_shows_details)
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    """ Venue create form """
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    """ Submit callback for venue create form  """
    # Get the form data
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    seeking_talent = request.form['seeking_talent'] == 'Yes'
    seeking_description = request.form['seeking_description']
    # genres is a list
    genres = request.form.getlist('genres')

    error = False
    form = VenueForm()
    # Validate form data
    if not form.validate_on_submit():
        flash(form.errors)
        # Redirect to the new_venue.html page with the error message in the above line
        return redirect(url_for('create_venue_submission'))

    try:
        # Create a venue instance using form data
        venue = Venue(
            name=name,
            city=city,
            state=state,
            address=address,
            phone=phone,
            image_link=image_link,
            facebook_link=facebook_link,
            website=website,
            seeking_talent=seeking_talent,
            seeking_description=seeking_description
        )
        db.session.add(venue)

        # Creating Venue generes instances and assigning using backref
        for genre in genres:
            new_genre = VenuesGenres(genre=genre)
            new_genre.venue = venue             # backref
            db.session.add(new_genre)

        db.session.commit()
    except Exception as err:
        print(err)
        db.session.rollback()
        error = True
    finally:
        db.session.close()

    if error:
        flash(f'An error occurred. Venue {name} could not be listed.')
        abort(500)

    flash(f'Venue {name} listed successfully')
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    """ Delete a venue by id """
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        flash('An error occurred while deleting the venue.')
        abort(500)
    flash('Venue was successfully deleted!')
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
    """ Get all artists """
    artists = Artist.query.all()
    data = [
        {
            'id': x.id,
            'name': x.name
        }
        for x in artists
    ]
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    """ Search for artist using search_term """
    search_term = request.form.get('search_term')
    # Reference: https://stackoverflow.com/questions/3325467/sqlalchemy-equivalent-to-sql-like-statement
    # Get all venues using LIKE sql statement
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    data = [
        {
            'id': x.id,
            'name': x.name,
            'num_upcoming_shows': len(x.upcoming_shows)
        }
        for x in artists
    ]
    response = {
        'count': len(data),
        'data': data
    }
    return render_template(
        'pages/search_artists.html',
        results=response,
        search_term=request.form.get('search_term', '')
    )


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    """ Get a artist by id """
    artist = Artist.query.get(artist_id)
    # Upcoming show details
    upcoming_shows_details = [
        {
            'artist_id': x.artist_id,
            'artist_name': x.artist.name,
            'artist_image_link': x.artist.image_link,
            'start_time': x.start_time.isoformat()
        }
        for x in artist.upcoming_shows
    ]

    # Past show details
    past_show_details = [
        {
            'venue_id': x.venue_id,
            'venue_name': x.venue.name,
            'venue_image_link': x.venue.image_link,
            'start_time': x.start_time.isoformat()
        }
        for x in artist.past_shows
    ]

    data = {
        'id': artist_id,
        'name': artist.name,
        'genres': artist.genres_list,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': past_show_details,
        'upcoming_shows': upcoming_shows_details,
        'past_shows_count': len(past_show_details),
        'upcoming_shows_count': len(upcoming_shows_details)
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    """ Edit a Artist """
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    # Prepopulate the form fields
    form.name.data = artist.name
    form.genres.data = artist.genres_list
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    """ Submit call back for edit artist form """
    # Get form data
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    seeking_venue = request.form['seeking_venue'] == 'Yes'
    seeking_description = request.form['seeking_description']
    # genres is a list
    genres = request.form.getlist('genres')

    form = ArtistForm()
    # Validate form data
    if not form.validate_on_submit():
        flash(form.errors)
        return redirect(url_for('edit_artist_submission'))

    error = False
    try:
        # Update artist instance with form data
        artist = Artist.query.get(artist_id)
        artist.name = name
        artist.city = city
        artist.state = state
        artist.phone = phone
        artist.image_link = image_link
        artist.facebook_link = facebook_link
        artist.website = website
        artist.seeking_venue = seeking_venue
        artist.seeking_description = seeking_description
        db.session.add(artist)

        # Delete old generes
        for x in artist.genres:
            db.session.delete(x)

        # Creating Artist generes instances and assigning using backref
        for genre in genres:
            new_genre = ArtistsGenres(genre=genre)
            new_genre.artist = artist  # backref
            db.session.add(new_genre)

        db.session.commit()
    except Exception as err:
        print(err)
        db.session.rollback()
        error = True
    finally:
        db.session.close()

    if error:
        flash(f'An error occurred. Artist {name} could not be updated.')
        abort(500)

    flash(f'Artist {name} updated successfully')
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    """ Venue edit form """
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    # Pre-populate form fields
    form.name.data = venue.name
    form.genres.data = venue.genres_list
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.website.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    """ Submit callback for edit venue form """
    # Get the form data
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    seeking_talent = request.form['seeking_talent'] == 'Yes'
    seeking_description = request.form['seeking_description']
    # genres is a list
    genres = request.form.getlist('genres')

    error = False
    form = VenueForm()
    # Validate form data
    if not form.validate_on_submit():
        flash(form.errors)
        # Redirect to the new_venue.html page with the error message in the above line
        return redirect(url_for('edit_venue_submission'))

    try:
        # Update venue instance with form data
        venue = Venue.query.get(venue_id)
        venue.name = name
        venue.city = city
        venue.state = state
        venue.address = address
        venue.phone = phone
        venue.image_link = image_link
        venue.facebook_link = facebook_link
        venue.website = website
        venue.seeking_talent = seeking_talent
        venue.seeking_description = seeking_description

        # Delete old generes
        [db.session.delete(x) for x in venue.genres]

        # Creating Venue generes instances and assigning using backref
        for genre in genres:
            new_genre = VenuesGenres(genre=genre)
            new_genre.venue = venue  # backref
            db.session.add(new_genre)

        db.session.commit()
    except Exception as err:
        print(err)
        db.session.rollback()
        error = True
    finally:
        db.session.close()

    if error:
        flash(f'An error occurred. Venue {name} could not be updated.')
        abort(500)

    flash(f'Venue {name} updated successfully')
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    """ Create artists """
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    """ Submit callback for create artists form """
    # Get form data
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    seeking_venue = request.form['seeking_venue'] == 'Yes'
    seeking_description = request.form['seeking_description']
    # genres is a list
    genres = request.form.getlist('genres')

    form = ArtistForm()
    # Validate form data
    if not form.validate_on_submit():
        flash(form.errors)
        return redirect(url_for('create_artist_submission'))

    error = False
    try:
        # Create a venue instance using form data
        artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            image_link=image_link,
            facebook_link=facebook_link,
            website=website,
            seeking_venue=seeking_venue,
            seeking_description=seeking_description
        )
        db.session.add(artist)

        # Creating Artist generes instances and assigning using backref
        for genre in genres:
            new_genre = ArtistsGenres(genre=genre)
            new_genre.artist = artist             # backref
            db.session.add(new_genre)

        db.session.commit()
    except Exception as err:
        print(err)
        db.session.rollback()
        error = True
    finally:
        db.session.close()

    if error:
        flash(f'An error occurred. Artist {name} could not be listed.')
        abort(500)

    flash(f'Artist {name} listed successfully')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    """ Get all shows """
    shows = Show.query.all()
    data = [
        {
            'venue_id': x.venue.id,
            'venue_name': x.venue.name,
            'artist_id': x.artist.id,
            'artist_name': x.artist.name,
            'artist_image_link': x.artist.image_link,
            'start_time': x.start_time.isoformat()
        }
        for x in shows
    ]
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    """ Create show form """
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    """ Submit callback for show form """
    # Get the form data
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    form = ShowForm()
    # Validate form data
    if not form.validate_on_submit():
        flash(form.errors)
        # Redirect to the new_show.html page with the error message in the above line
        return redirect(url_for('create_show_submission'))

    error = False
    venue = Venue.query.get(venue_id)
    artist = Artist.query.get(artist_id)

    # Check if the venue id exists or not.
    if venue is None:
        flash('The venue id ' + venue_id + ' does not exist')
        return redirect(url_for('create_show_submission'))

    # Check if the artist id exists or not.
    if artist is None:
        flash('The artist id ' + artist_id + ' does not exist')
        return redirect(url_for('create_show_submission'))

    try:
        # Create Show instance using form data
        show = Show(venue_id=venue_id,
                    artist_id=artist_id,
                    start_time=start_time)
        db.session.add(show)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
    finally:
        db.session.close()

    if error:
        flash(f'An error occurred. Show could not be listed')
        abort(500)
    else:
        flash(f'Show listed successfully')
        return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
