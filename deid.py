from deid.dicom import replace_identifiers
from deid.dicom import get_identifiers
from deid.config import DeidRecipe
import os

output_folder = 'test_deid_out'
input_folder = 'test_deid'

dicom_files = [os.path.join(input_folder, dicom_file) for dicom_file in os.listdir(input_folder)]
ids = get_identifiers(dicom_files)
recipe = DeidRecipe('deid.conf')

# or use default conf, and then keep AccessionNumber
recipe = DeidRecipe()
recipe.deid['header'].remove({'action': 'REMOVE', 'field': 'AccessionNumber'})

updated_ids = dict()
for image, fields in ids.items():
    fields['id'] = 'cookiemonster'
    fields['source_id'] = "cookiemonster-image-%s" %(count)
    updated_ids[os.path.basename(image)] = fields

cleaned_files = replace_identifiers(dicom_files=dicom_files,
                                    deid=recipe,
                                    ids=updated_ids,
                                    output_folder=output_folder)

"""
from pydicom import dcmread
ds = dcmread(os.path.join(output_folder, 'CR.1.2.392.200046.100.2.1.207458824283835.150629135224.1.1.1.1'))
ds = dcmread(os.path.join(input_folder, 'CR.1.2.392.200046.100.2.1.207458824283835.150629135224.1.1.1.1'))
"""
