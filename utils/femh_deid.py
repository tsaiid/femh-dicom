from deid.dicom import replace_identifiers
from deid.dicom import get_identifiers
from deid.config import DeidRecipe
from os import listdir, makedirs
from os.path import join, exists, dirname, basename
import sys
import errno

def main():
    if len(sys.argv) is not 3:
        print("argv")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]

    dicom_files = [join(input_folder, dicom_file) for dicom_file in listdir(input_folder)]
    ids = get_identifiers(dicom_files)

    # or use default conf, and then keep AccessionNumber
    #recipe = DeidRecipe('deid.conf')
    recipe = DeidRecipe()
    #recipe.deid['header'].remove({'action': 'REMOVE', 'field': 'AccessionNumber'})
    recipe.deid['header'].append({'action': 'REMOVE', 'field': 'InstitutionName'})

    updated_ids = dict()
    for image, fields in ids.items():
        #fields['id'] = 'cookiemonster'
        #fields['source_id'] = "cookiemonster-image-%s" %(count)
        updated_ids[basename(image)] = fields

    if not exists(output_folder):
        try:
            makedirs(output_folder)
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    cleaned_files = replace_identifiers(dicom_files=dicom_files,
                                        deid=recipe,
                                        ids=updated_ids,
                                        output_folder=output_folder)

if __name__ == "__main__":
    main()
