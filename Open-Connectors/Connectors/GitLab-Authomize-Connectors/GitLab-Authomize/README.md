# Authomize Sync

A command-line utility for reading user and permission information from third-party service APIs and uploading them to Authomize.

Please see the [deployment project][] for configuration and deployment information.

[deployment project]: https://gitlab.com/gitlab-private/gl-security/engineering-and-research/automation-team/kubernetes/secauto/authomize

## Using the CLI

The CLI is built with [Click](https://pocoo-click.readthedocs.io/) and is self-documenting.

To get help, use the `--help` option with any command:

```bash
python main.py --help
```

## Development

Running sync jobs requires various credentials to be set in the environment. See the `sample.env` file for descriptions of the environment variables.

```bash
# Activate virtual environment
pipenv shell
# Install dependencies
pipenv install -d
# Sync a single Connector **without** uploading to Authomize
./main.py sync --test ava-tax
# Sync a single connector and upload to Authomize
./main.py sync ava-tax
# Sync all Connectors and upload to Authomize
./main.py sync all
```

Running in Docker:

Note: When using `sample.env` as a docker env file, comment out `set -a` in the first line of the file.

```bash
# Build the Docker image
docker build -t authomize .
# Run in Docker
docker run -it --rm --env-file .env authomize sync --test ava-tax
```

## Creating a New Connector

Each connector should be its own module file in the `connectors` directory. Each connector must implement a class that inherits from the `Base` class and implements the `collect` method. To keep consistent with convention it would be preferable to name the class `Connector`. Additionally, it is important to note that the `CONNECTOR_ID` will be what is displayed in the Authomize UI and camel case is the preferred syntax.

```python
from connectors import Base

CONNECTOR_ID = "FooBar"


class Connector(Base):
    """Authomize connector for FooBar.

    TODO Add link to FooBar API docs.
    """

    def __init__(self):
        super().__init__(CONNECTOR_ID)

    def collect(self) -> dict:
        result = {}
        # ...
        return result
```

The `collect` method returns a dictionary of the data type and an iterator for the data associated with that data type. Refer to the `ItemsBundleSchema` in the generated [schema.py](https://github.com/authomize/connectors-rest-api-client/blob/master/authomize/rest_api_client/generated/schemas.py) file to identify the data types required for each steerable. The keys for each of data type are inherited from the `Base` class, so if a connector was retrieving identities the returned dictionary would look like `{self.IDENTITY: Iterator[IdentityDescription]}`.

**Please note:** our current approach to handling unexpected input from the third-party service is to "fail closed". For example, when a user role in the third-party service has not been mapped to Authomize yet, the connector should raise an exception (i.e. by failing a dictionary lookup), rather than use a default value. This is intended to prevent access reviews based on potentially incorrect data, and give us the ability to detect problems early in the `dev` environment, instead of during access reviews in the `live` environment.

In order to make the new connector available in the CLI, a method should be added to `main.py`, associated with the `sync` group. In our example of the `FooBar` connector, we would implement a method that looks like this:

```python
from connectors import (
    # ...
    foo_bar,
    # ...
)

# ...

@sync.command(name="foo-bar")
def sync_foo_bar():
    """Sync data from FooBar to Authomize."""
    foo_bar.Connector().run()

```

The connector can now be tested by running `python main.py sync --test foo-bar`
