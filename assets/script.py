from oysterpail.takeout import mail
import pickle
import click
import pandas as pd


def mail_text_handler(m):
    """Returns mail text"""
    return {"mail_text": mail._get_mail_text(m)}


def extract_mail(input_f, output_f):
    """Extract mail content and features"""
    # add a new handler
    mail._mail_handlers.append(mail_text_handler)

    # process mails
    mail.main(input_f, output_f)


def convert_mail(input_f, output_f):
    """Save only sent mails as a dataframe"""

    with open(input_f, "rb") as f:
        mails = pickle.load(f)

    sent_mails = [m for m in mails if m["is_sent"]]
    df = pd.DataFrame(sent_mails)
    df.to_pickle(output_f)


@click.command()
@click.option(
    "-c",
    "--command",
    type=click.Choice(["extract", "convert"]),
    required=True,
    help="Command types. `extract` for retrieving mails. `convert`: to filter sent mails in a dataframe",
)
@click.option(
    "-i",
    "--input",
    "input_f",
    required=True,
    type=click.Path(exists=True),
    help="Input file path",
)
@click.option(
    "-o",
    "--output",
    "output_f",
    required=True,
    type=click.Path(),
    help="Output file path",
)
def cli(command, input_f, output_f):
    if command == "extract":
        extract_mail(input_f, output_f)
    elif command == "convert":
        convert_mail(input_f, output_f)
    else:
        raise ValueError("Unknown command: {0}".format(command))


if __name__ == "__main__":
    cli()
