import os
import re
import shutil
import tempfile

from pathlib import Path

import pandas as pd

from azure.identity import (
    DefaultAzureCredential
)

from azure.storage.blob import (
    BlobServiceClient
)

from azure.core.exceptions import (
    ResourceExistsError,
    ResourceNotFoundError
)

from config import (
    UPLOAD_FOLDER,
    CLEANED_FOLDER,
    REPORT_FOLDER
)


# =========================================================
# STORAGE CONFIGURATION
# =========================================================

STORAGE_MODE = os.getenv(
    "STORAGE_MODE",
    "local"
).strip().lower()


AZURE_STORAGE_ACCOUNT_URL = os.getenv(
    "AZURE_STORAGE_ACCOUNT_URL",
    ""
).strip()


AZURE_STORAGE_CONTAINER = os.getenv(
    "AZURE_STORAGE_CONTAINER",
    "dataforge"
).strip()


# =========================================================
# VALID STORAGE TYPES
# =========================================================

VALID_STORAGE_TYPES = {
    "uploads",
    "cleaned",
    "reports"
}


# =========================================================
# SAFE FILENAME
# =========================================================

def safe_filename(
    filename
):

    if not filename:

        return "file"

    filename = os.path.basename(
        str(filename)
    )

    filename = re.sub(
        r"[^a-zA-Z0-9._-]+",
        "_",
        filename
    )

    if not filename:

        filename = "file"

    return filename


# =========================================================
# VALIDATE STORAGE TYPE
# =========================================================

def validate_storage_type(
    storage_type
):

    if storage_type not in VALID_STORAGE_TYPES:

        raise ValueError(
            f"Unknown storage type: {storage_type}"
        )


# =========================================================
# LOCAL STORAGE DIRECTORY
# =========================================================

def get_storage_folder(
    storage_type
):

    validate_storage_type(
        storage_type
    )

    folders = {
        "uploads":
            UPLOAD_FOLDER,

        "cleaned":
            CLEANED_FOLDER,

        "reports":
            REPORT_FOLDER
    }

    folder = folders[
        storage_type
    ]

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return folder


# =========================================================
# LOCAL FILE PATH
# =========================================================

def get_local_file_path(
    storage_type,
    filename
):

    folder = get_storage_folder(
        storage_type
    )

    filename = safe_filename(
        filename
    )

    return (
        folder
        /
        filename
    )


# =========================================================
# AZURE BLOB NAME
# =========================================================

def get_blob_name(
    storage_type,
    filename
):

    validate_storage_type(
        storage_type
    )

    filename = safe_filename(
        filename
    )

    return (
        f"{storage_type}/"
        f"{filename}"
    )


# =========================================================
# AZURE BLOB SERVICE CLIENT
# =========================================================

def get_blob_service_client():

    if not AZURE_STORAGE_ACCOUNT_URL:

        raise ValueError(
            "AZURE_STORAGE_ACCOUNT_URL "
            "is not configured."
        )

    credential = (
        DefaultAzureCredential()
    )

    return BlobServiceClient(
        account_url=
            AZURE_STORAGE_ACCOUNT_URL,
        credential=
            credential
    )


# =========================================================
# AZURE CONTAINER CLIENT
# =========================================================

def get_azure_container_client():

    service_client = (
        get_blob_service_client()
    )

    container_client = (
        service_client
        .get_container_client(
            AZURE_STORAGE_CONTAINER
        )
    )

    return container_client


# =========================================================
# CREATE AZURE CONTAINER IF NEEDED
# =========================================================

def ensure_azure_container():

    container_client = (
        get_azure_container_client()
    )

    try:

        container_client.create_container()

    except ResourceExistsError:

        pass

    return container_client


# =========================================================
# SAVE BYTES TO AZURE
# =========================================================

def save_bytes_to_azure(
    storage_type,
    filename,
    data
):

    container_client = (
        ensure_azure_container()
    )

    blob_name = get_blob_name(
        storage_type,
        filename
    )

    blob_client = (
        container_client
        .get_blob_client(
            blob_name
        )
    )

    blob_client.upload_blob(
        data,
        overwrite=True
    )

    return blob_name

# =========================================================
# DOWNLOAD AZURE BLOB TO LOCAL CACHE
#
# Pandas and several DataForge loaders currently operate
# using filesystem paths. In Azure mode this method
# downloads the requested blob to a temporary local path.
# =========================================================

def download_azure_to_local(
    storage_type,
    filename
):

    container_client = (
        get_azure_container_client()
    )

    blob_name = get_blob_name(
        storage_type,
        filename
    )

    blob_client = (
        container_client
        .get_blob_client(
            blob_name
        )
    )

    filename = safe_filename(
        filename
    )

    cache_root = Path(
        tempfile.gettempdir()
    ) / "dataforge_storage"

    cache_folder = (
        cache_root
        /
        storage_type
    )

    cache_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    local_path = (
        cache_folder
        /
        filename
    )

    try:

        blob_data = (
            blob_client
            .download_blob()
            .readall()
        )

    except ResourceNotFoundError:

        raise FileNotFoundError(
            f"Azure blob not found: {blob_name}"
        )


    with open(
        local_path,
        "wb"
    ) as file_handle:

        file_handle.write(
            blob_data
        )

    return local_path


# =========================================================
# GET FILE PATH
#
# Local mode:
# Returns the normal filesystem path.
#
# Azure mode:
# Downloads the blob to the DataForge temporary cache
# and returns that local path.
# =========================================================

def get_file_path(
    storage_type,
    filename
):

    if STORAGE_MODE == "azure":

        return download_azure_to_local(
            storage_type,
            filename
        )

    return get_local_file_path(
        storage_type,
        filename
    )


# =========================================================
# SAVE BYTES
# =========================================================

def save_bytes(
    storage_type,
    filename,
    data
):

    if STORAGE_MODE == "azure":

        save_bytes_to_azure(
            storage_type,
            filename,
            data
        )

        # Return a local cached version so existing
        # DataForge processing code can continue using
        # filesystem paths.

        local_path = get_local_file_path(
            storage_type,
            filename
        )

        with open(
            local_path,
            "wb"
        ) as file_handle:

            file_handle.write(
                data
            )

        return local_path


    filepath = get_local_file_path(
        storage_type,
        filename
    )

    with open(
        filepath,
        "wb"
    ) as file_handle:

        file_handle.write(
            data
        )

    return filepath


# =========================================================
# SAVE EXISTING FILE
# =========================================================

def save_file(
    storage_type,
    filename,
    source_path
):

    validate_storage_type(
        storage_type
    )

    filename = safe_filename(
        filename
    )


    if STORAGE_MODE == "azure":

        with open(
            source_path,
            "rb"
        ) as file_handle:

            data = file_handle.read()

        save_bytes_to_azure(
            storage_type,
            filename,
            data
        )

        return get_blob_name(
            storage_type,
            filename
        )


    destination = (
        get_local_file_path(
            storage_type,
            filename
        )
    )

    shutil.copy2(
        source_path,
        destination
    )

    return destination


# =========================================================
# SAVE DATAFRAME
# =========================================================

def save_dataframe(
    storage_type,
    filename,
    dataframe
):

    filename = safe_filename(
        filename
    )

    extension = (
        Path(
            filename
        )
        .suffix
        .lower()
    )


    if extension not in {
        ".csv",
        ".xlsx"
    }:

        raise ValueError(
            f"Unsupported export format: {extension}"
        )


    # -----------------------------------------------------
    # Azure
    # -----------------------------------------------------

    if STORAGE_MODE == "azure":

        temporary_folder = Path(
            tempfile.gettempdir()
        ) / "dataforge_exports"

        temporary_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        temporary_path = (
            temporary_folder
            /
            filename
        )


        if extension == ".xlsx":

            dataframe.to_excel(
                temporary_path,
                index=False,
                engine="openpyxl"
            )

        else:

            dataframe.to_csv(
                temporary_path,
                index=False,
                encoding="utf-8"
            )


        with open(
            temporary_path,
            "rb"
        ) as file_handle:

            file_data = (
                file_handle.read()
            )


        save_bytes_to_azure(
            storage_type,
            filename,
            file_data
        )


        return temporary_path


    # -----------------------------------------------------
    # Local
    # -----------------------------------------------------

    filepath = get_local_file_path(
        storage_type,
        filename
    )


    if extension == ".xlsx":

        dataframe.to_excel(
            filepath,
            index=False,
            engine="openpyxl"
        )

    else:

        dataframe.to_csv(
            filepath,
            index=False,
            encoding="utf-8"
        )


    return filepath

# =========================================================
# FILE EXISTS
# =========================================================

def file_exists(
    storage_type,
    filename
):

    validate_storage_type(
        storage_type
    )


    if STORAGE_MODE == "azure":

        container_client = (
            get_azure_container_client()
        )

        blob_name = get_blob_name(
            storage_type,
            filename
        )

        blob_client = (
            container_client
            .get_blob_client(
                blob_name
            )
        )

        return blob_client.exists()


    filepath = get_local_file_path(
        storage_type,
        filename
    )

    return filepath.is_file()


# =========================================================
# GET FILE SIZE
# =========================================================

def get_file_size(
    storage_type,
    filename
):

    validate_storage_type(
        storage_type
    )


    if STORAGE_MODE == "azure":

        container_client = (
            get_azure_container_client()
        )

        blob_name = get_blob_name(
            storage_type,
            filename
        )

        blob_client = (
            container_client
            .get_blob_client(
                blob_name
            )
        )


        try:

            properties = (
                blob_client
                .get_blob_properties()
            )

            return int(
                properties.size
                or 0
            )

        except ResourceNotFoundError:

            return 0


    filepath = get_local_file_path(
        storage_type,
        filename
    )


    if not filepath.is_file():

        return 0


    return filepath.stat().st_size


# =========================================================
# DELETE FILE
# =========================================================

def delete_file(
    storage_type,
    filename
):

    validate_storage_type(
        storage_type
    )


    if STORAGE_MODE == "azure":

        container_client = (
            get_azure_container_client()
        )

        blob_name = get_blob_name(
            storage_type,
            filename
        )

        blob_client = (
            container_client
            .get_blob_client(
                blob_name
            )
        )


        try:

            blob_client.delete_blob()

            return True

        except ResourceNotFoundError:

            return False


    filepath = get_local_file_path(
        storage_type,
        filename
    )


    if filepath.is_file():

        filepath.unlink()

        return True


    return False


# =========================================================
# LIST FILES
# =========================================================

def list_files(
    storage_type
):

    validate_storage_type(
        storage_type
    )


    if STORAGE_MODE == "azure":

        container_client = (
            get_azure_container_client()
        )

        prefix = (
            f"{storage_type}/"
        )

        files = []

        for blob in container_client.list_blobs(
            name_starts_with=prefix
        ):

            name = blob.name

            if name.startswith(
                prefix
            ):

                name = name[
                    len(prefix):
                ]

            if name:

                files.append(
                    name
                )

        return files


    folder = get_storage_folder(
        storage_type
    )

    return [
        file.name
        for file in folder.iterdir()
        if file.is_file()
    ]

# =========================================================
# STORAGE HEALTH
# =========================================================

def check_storage():

    # -----------------------------------------------------
    # Azure
    # -----------------------------------------------------

    if STORAGE_MODE == "azure":

        try:

            container_client = (
                get_azure_container_client()
            )

            container_client.get_container_properties()

            return True

        except Exception:

            return False


    # -----------------------------------------------------
    # Local
    # -----------------------------------------------------

    try:

        for folder in [
            UPLOAD_FOLDER,
            CLEANED_FOLDER,
            REPORT_FOLDER
        ]:

            folder.mkdir(
                parents=True,
                exist_ok=True
            )

            if not folder.is_dir():

                return False


        return True

    except Exception:

        return False


# =========================================================
# STORAGE MODE
# =========================================================

def get_storage_mode():

    return STORAGE_MODE