import os
import glob
import yaml
import markdown
import json
import datetime

# TODO reformat for less indentation
# TODO error handling for bad yaml


class Reader:
    def __init__(self):
        self.md = markdown.Markdown(extensions=['markdown.extensions.fenced_code'])

    def read(self, data_dir):
        # Walk through the directory {data_dir}. Any folders there become top
        # level elements in our data. Any .yml files there will be parsed into
        # results

        all_data = {}
        for data_type in os.listdir(data_dir):
            all_data[data_type] = []
            for file_name in glob.glob('%s/%s/*.yml' % (data_dir, data_type)):
                # Read the file as YAML
                f = open(file_name, 'r')
                data = yaml.load(f)
                f.close()
                if data is None:
                    continue

                # The file's basename is its id
                basename = os.path.splitext(os.path.basename(file_name))[0]
                data['_id'] = basename

                # If the special markdown key is present parse it's properties
                # as markdown files and place the output on the root object.
                # Files are assumed to be adjacent to the yaml file in the
                # filesystem
                if '_markdown' in data:
                    for prop in data['_markdown']:
                        markdown_file = '%s/%s' % (os.path.dirname(file_name), data['_markdown'][prop])
                        with open(markdown_file) as f:
                            data[prop] = self.md.convert(f.read())

                    del data['_markdown']

                all_data[data_type].append(data)

        return all_data


class Writer:
    class PysagJson(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime.date):
                return str(obj)
            return json.JSONEncoder.default(self, obj)

    def _write_json(self, data, path):
        with open(path, 'w') as f:
            json.dump({'result': data}, f, cls=self.PysagJson)

    def write_api(self, data, output_dir):
        for key in data:
            all_data = []
            dir = '%s/%s' % (output_dir, key)
            if not os.path.isdir(dir):
                os.makedirs(dir)
            for node in data[key]:
                all_data.append(node)
                path = '%s/%s/%s.json' % (output_dir, key, node['_id'])
                self._write_json(node, path)

            path = '%s/%s.json' % (output_dir, key)
            self._write_json(all_data, path)
