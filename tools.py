import click
from SPARQLWrapper import SPARQLWrapper, JSON
import json


PERSONS_QUERY = 'sparql/persons.sparql'
TYPES_QUERY = 'sparql/types.sparql'
ABSTRACTS_QUERY = 'sparql/abstracts.sparql'
END_POINT = 'http://ja.dbpedia.org/sparql'


def get_data(query):
    sparql = SPARQLWrapper(END_POINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results['results']['bindings']


def to_json(data):
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


@click.group()
def cmd():
    pass


@cmd.command()
@click.option('--dist', default='dist.json', type=click.STRING)
def persons(dist):
    data = get_data(open(PERSONS_QUERY).read())
    data = [d['person']['value'] for d in data]
    with open(dist, 'w') as fp:
        fp.write(to_json(data))


@cmd.command()
@click.argument('persons_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--dist', default='dist.json', type=click.STRING)
def types(persons_path, dist):
    result = {}

    query = open(TYPES_QUERY).read()
    person_uris = json.load(open(persons_path))
    number_of_query = len(person_uris)
    for idx, person in enumerate(person_uris):
        click.echo('{}/{}'.format(idx, number_of_query))
        data = get_data(query.format(person))
        data = {d['type_label']['value'] for d in data if d['type_label'].get('xml:lang') == 'en'}
        result[person] = list(data)
    with open(dist, 'w') as fp:
        fp.write(to_json(result))


@cmd.command()
@click.argument('persons_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--dist', default='dist.json', type=click.STRING)
@click.option('--from_count', default=0, type=click.INT)
def abstracts(persons_path, dist, from_count):
    result = {}
    query = open(ABSTRACTS_QUERY).read()
    person_uris = json.load(open(persons_path))
    person_uris = person_uris[from_count:]
    number_of_query = len(person_uris)
    try:
        for idx, person in enumerate(person_uris):
            click.echo('{}/{}'.format(idx, number_of_query))
            data = get_data(query.format(person))
            data = [d['abstract']['value'] for d in data]
            result[person] = data
    finally:
        with open(dist, 'w') as fp:
            fp.write(to_json(result))


@cmd.command()
@click.argument('person_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.argument('abstracts_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.argument('types_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
def make_dataset(person_path, abstracts_path, types_path):
    abstracts_dict = json.load(open(abstracts_path))
    types_dict = json.load(open(types_path))
    dataset = {}
    for person in json.load(open(person_path)):
        abstract = abstracts_dict.get(person)
        if not abstract:
            continue
        types_list = types_dict[person]
        dataset[abstract] = types_list


if __name__ == '__main__':
    cmd()
