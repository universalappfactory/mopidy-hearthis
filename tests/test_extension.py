from datetime import datetime

from pyhearthis.models import SingleTrack, User

from mopidy_hearthis import Extension
from mopidy_hearthis.hearthis_search import ModelCache, ModelFactory


def test_get_default_config():
    ext = Extension()

    config = ext.get_default_config()

    assert "[hearthis]" in config
    assert "enabled = true" in config


def test_get_config_schema():
    ext = Extension()

    schema = ext.get_config_schema()

    assert "username" in schema
    assert "password" in schema


def create_track(id, user_id, title) -> SingleTrack:
    dt = datetime(2021, 2, 2)
    user = User(user_id, "", "", "", "", "", "")
    return SingleTrack(
        id,
        dt,
        0,
        None,
        None,
        "",
        user_id,
        0,
        "",
        "",
        1,
        "",
        "",
        title,
        "uri",
        "permalink",
        "thumb",
        "artwork",
        "background",
        "wave",
        "wave_url",
        user,
        "strean_url",
        "download",
        1,
        1,
        1,
        False,
        1,
        "",
        "",
        1,
        "",
        "type",
        "license",
        "versio",
        "",
        "",
        "",
        1,
        False,
        False,
        False,
    )


def test_that_modelfactory_creates_expected_result():
    # Arrange
    first_track = create_track(1, 101, "Track 1")
    second_track = create_track(2, 201, "Track 2")
    tracks = [first_track, second_track]

    # Act
    result = ModelFactory.create_track_models(tracks)

    # Assert
    assert result is not None
    assert len(result) == 2
    tuple1 = result[0]
    tuple2 = result[1]
    assert tuple1[1].single_track.title == "Track 1"
    assert tuple2[1].single_track.title == "Track 2"


def test_that_model_cache_get_artist_tracks_returns_expected_data():
    # Arrange
    sut = ModelCache()
    first_track = create_track(1, 101, "Track 1")
    second_track = create_track(2, 201, "Track 2")
    tracks = [first_track, second_track]
    models = ModelFactory.create_track_models(tracks)
    sut.add_models(models)

    # Act
    result = sut.get_artist_tracks("hearthis:artist:101")

    # Assert
    assert result is not None
    assert len(result) == 1
    track = result[0]
    assert track.single_track.title == "Track 1"


def test_that_model_cache_get_artist_returns_expected_data():
    # Arrange
    sut = ModelCache()
    first_track = create_track(1, 101, "Track 1")
    second_track = create_track(2, 201, "Track 2")
    tracks = [first_track, second_track]
    models = ModelFactory.create_track_models(tracks)
    sut.add_models(models)

    # Act
    result = sut.get_artist("hearthis:artist:101")

    # Assert
    assert result is not None
    assert result.uri == "hearthis:artist:101"


def test_that_model_cache_artist_tracks_complete_returns_expected_data():
    # Arrange
    sut = ModelCache()
    first_track = create_track(1, 101, "Track 1")
    second_track = create_track(2, 201, "Track 2")
    third_track = create_track(2, 101, "Track 3")
    tracks = [first_track, second_track]
    models = ModelFactory.create_track_models(tracks)
    sut.add_models(models)

    # Act
    result = sut.artist_tracks_complete("hearthis:artist:101")

    # Assert
    assert result is False

    # Add third track
    tracks = ModelFactory.create_track_models([third_track])
    sut.add_models(tracks, True)
    result = sut.artist_tracks_complete("hearthis:artist:101")

    assert result is True


def test_that_model_cache_add_models_adds_expected_artist_tracks():
    # Arrange
    sut = ModelCache()
    first_track = create_track(1, 101, "Track 1")
    second_track = create_track(2, 201, "Track 2")
    third_track = create_track(2, 101, "Track 3")
    tracks = [first_track, second_track]
    models = ModelFactory.create_track_models(tracks)
    sut.add_models(models)

    # Act
    result = sut.get_artist_tracks("hearthis:artist:101")

    # Assert
    assert len(result) == 1

    # Add third track
    tracks = ModelFactory.create_track_models([third_track])
    sut.add_models(tracks, True)
    result = sut.get_artist_tracks("hearthis:artist:101")

    assert len(result) == 2


def test_that_model_cache_get_track_returns_expected_data():
    # Arrange
    sut = ModelCache()
    first_track = create_track(1, 101, "Track 1")
    # second_track = create_track(2,201, "Track 2")
    tracks = [first_track]
    models = ModelFactory.create_track_models(tracks)
    sut.add_models(models)

    # Act
    result = sut.get_track(first_track.stream_url)

    # Assert
    assert result is not None


def test_that_get_artist_tracks_returns_expected_data():
    pass
