import glob
import pathlib

import yaml
import click

from fontTools.ttLib import TTFont


# ----------------------------------------


def walk_path(path):
    file_types = [".otf", ".ttf", ".woff", ".woff2"]
    path = pathlib.Path(path)
    if not path.exists():
        raise FileNotFoundError(f"'{path}' does not exist")
        return []
    if path.is_dir():
        fonts = []
        for ext in file_types:
            fonts += path.glob("*" + ext)
        return fonts
    if path.is_file():
        assert path.suffix in file_types, f"{path.name} is not a font file"
        return [path]


def _load_yaml_data(yaml_path):
    with open(yaml_path, "r") as yaml_file:
        return yaml.load(yaml_file.read(), yaml.SafeLoader)


# ----------------------------------------

def inject_vertical_metrics(font, data_):
    print(font["name"].getDebugName(4))
    for k in data_.keys():
        table = font[k]
        for attribute, value in data_[k].items():
            setattr(table, attribute, value)
            print(f"-- {k} {attribute}: {value}")


def vertical_metrics_inject_in_fonts(input_path, yaml_path, output_dir=None):
    yaml_path = pathlib.Path(yaml_path)
    input_path = pathlib.Path(input_path)
    print(f"Injecting '{yaml_path.name}' to '{input_path.name}' ")
    font_paths = walk_path(input_path)
    data_ = _load_yaml_data(yaml_path)
    for p in font_paths:
        font = TTFont(p)
        inject_vertical_metrics(font, data_)
        if output_dir:
            output_dir = pathlib.Path(output_dir)
            output_dir = p.parent / output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / p.name
        else:
            out_path = p
        font.save(out_path)
        print(f"saved as '{out_path.relative_to(input_path)}'")

        print("")
    print("Done")


@click.command()
@click.option('-o', '--output_dir', default=None)
@click.argument("input_path", type=click.Path(exists=False))
@click.argument("yaml_path", type=click.Path(exists=False))
def vertical_metrics_inject_in_fonts_wrapper(input_path, yaml_path, output_dir):
    vertical_metrics_inject_in_fonts(input_path, yaml_path, output_dir)
