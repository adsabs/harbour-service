"""
Contains useful functions and utilities that are not neccessarily only useful
for this module. But are also used in differing modules insidide the same
project, and so do not belong to anything specific.
"""


def get_post_data(request, types={}):
    """
    Attempt to coerce POST json data from the request, falling
    back to the raw data if json could not be coerced.
    :param request: flask.request
    :param types: types that the incoming request object must cohere to
    """
    try:
        post_data = request.get_json(force=True)
    except:
        post_data = request.values

    if types and isinstance(post_data, dict):
        for expected_key in types:
            if expected_key not in post_data.keys():
                continue

            if not isinstance(post_data[expected_key],
                              types[expected_key]):
                raise TypeError(
                    '{0} should be type {1} but is {2}'
                    .format(expected_key,
                            types[expected_key],
                            type(post_data[expected_key]))
                )

    return post_data


def err(error_dictionary):
    """
    Formats the error response as wanted by the Flask app
    :param error_dictionary: name of the error dictionary
    :return: tuple of error message and error number
    """
    return {'error': error_dictionary['message']}, error_dictionary['code']
