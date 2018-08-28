
SCHEMA = {
    'type': 'object',
    'required': ['data'],
    'properties': {
        'data': {
            'type': 'object',
            'properties': {
                'files': {  # path to files
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Path to files to process.'
                },
                'directories': {  # path to directories to process
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Path to directories to process.'
                },
                'filetypes': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Limit only to specified filetypes.'
                }
            }
        },
        'workspace': {
            'type': 'string',
            'description': 'Path to do work and save results.'
        }
    }
}
