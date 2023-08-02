"""Console script for llm_stack."""
import subprocess
import sys

import click

from llm_stack import __version__
from llm_stack.config import ConfigLoader
from llm_stack.constants import (
    CUSTOM_MODEL_KEY_NAME,
    MODEL_CONFIG_KEY,
    RETRIEVER_CONFIG_KEY,
    VECTORDB_CONFIG_KEY,
)
from llm_stack.utils.run import execute_command_in_directory
from llm_stack.constants.model import AVAILABLE_MODEL_MAPS
from llm_stack.etl.run import run_etl_loader
from llm_stack.exception import LLMStackException
from llm_stack.model.run import (
    get_model_class,
    get_retriever_class,
    get_vectordb_class,
    list_supported_models,
    run_custom_model,
)

BANNER = """
██╗     ██╗     ███╗   ███╗    ███████╗████████╗ █████╗  ██████╗██╗  ██╗
██║     ██║     ████╗ ████║    ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
██║     ██║     ██╔████╔██║    ███████╗   ██║   ███████║██║     █████╔╝
██║     ██║     ██║╚██╔╝██║    ╚════██║   ██║   ██╔══██║██║     ██╔═██╗
███████╗███████╗██║ ╚═╝ ██║    ███████║   ██║   ██║  ██║╚██████╗██║  ██╗
╚══════╝╚══════╝╚═╝     ╚═╝    ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
"""


class LLMStackCommand(click.Group):
    def get_help(self, ctx: click.Context) -> str:
        return f"{BANNER}{super().get_help(ctx)}"


@click.group(cls=LLMStackCommand)
def main():
    click.echo(BANNER)


@main.command()
def version():
    """Version of the installed LLM Stack package

    `llmstack version`
    """
    click.echo(f"Version - {__version__}")


@main.command()
def list_models():
    """Lists available prebuilt models

    `llmstack list-models`
    """
    click.echo("Available List of models\n")
    for indx, model in enumerate(list_supported_models()):
        click.echo(f"{indx+1}. {model}")


@main.command()
@click.option("--config_file", help="Config file", type=str)
def start(config_file):
    """Start a HTTP server for a model

    `llmstack start --model gpt3.5`
    """

    config_loader = ConfigLoader(config=config_file)

    vectordb_client = get_vectordb_class(
        config_loader.get_config_section_name(
            VECTORDB_CONFIG_KEY,
        )
    )(config=config_file)
    retriever = get_retriever_class(
        config_loader.get_config_section_name(
            RETRIEVER_CONFIG_KEY,
        )
    )(config=config_file, vectordb=vectordb_client)

    model: str = config_loader.get_config_section_name(MODEL_CONFIG_KEY)
    model = model.strip()
    if model == CUSTOM_MODEL_KEY_NAME:
        return run_custom_model(
            config_loader=config_loader,
            retriver=retriever,
            config_file=config_file,
        )
    if model not in AVAILABLE_MODEL_MAPS.keys():
        raise LLMStackException(
            "Unkown Prebuilt Model Provided. Checkout how to run a custom model with LLM Stack."  # noqa: E501
        )
    model_class = get_model_class(model)(config=config_file, retriever=retriever)
    model_class.run_http_server()


@main.command()
@click.option("--config_file", help="Config file", type=str)
def etl(config_file):
    run_etl_loader(config_file=config_file)


@main.command()
@click.option(
    "-destination",
    help="Download and Install Airbyte",
    type=str,
    required=True,
)
def dli_airbyte(destination):
    click.echo("Downloading and installing Airbyte")
    execute_command_in_directory(
        target_directory=destination,
        commands=[
            "git clone https://github.com/airbytehq/airbyte.git",
            "cd airbyte",
            "./run-ab-platform.sh",
        ],
    )


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover