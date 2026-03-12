import os
from os import path
import Albus_RINEX



# --- Debug Mode ---
DEBUG_SET = False


def clean_mk_rnx2_file(in_filename, keep_backup=False):
    """
    Clean an original MeerKAT RINEX2 observation file using gfzrnx for proper ALBUS parsing.

    Input must follow pattern:
        MK01xxxx.yy[o]

    Output file will have the station code lowercased:
        mk01xxxx.yy[o]

    Also forces MARKER NAME in header from SEPT to GNSS standard convention MK01.
    """

    print("clean_mk_rnx2: in_filename:", in_filename)

    if not path.isfile(in_filename):
        raise Albus_RINEX.No_RINEX_File_Error(
            f"Input file not found: {in_filename}"
        )

    # ---- derive filenames ----
    dirname = path.dirname(in_filename)
    basename = path.basename(in_filename)

    # final filename = lowercase
    final_basename = basename.lower()
    final_output = path.join(dirname, final_basename)

    pass1_filename = in_filename + "_qcpass1"
    final_tmp_filename = in_filename + "_albus_tmp"
    backup_filename = in_filename + "_orig"

    if DEBUG_SET:
        print("clean_mk_rnx2: final output will be:", final_output)

    # optional backup
    if keep_backup:
        command = "cp %s %s" % (in_filename, backup_filename)
        print("clean_mk_rnx2: saving backup:", command)
        retcode = os.system(command)
        if retcode:
            raise Albus_RINEX.No_RINEX_File_Error(
                f"Could not execute '{command}'"
            )

    try:
        # ---------- Pass 1 ----------
        command = "gfzrnx -finp %s -fout %s -chk -kv" % (
            in_filename, pass1_filename)
        if DEBUG_SET:
            print("clean_mk_rnx2: executing command", command)
        retcode = os.system(command)
        if retcode:
            raise Albus_RINEX.No_RINEX_File_Error(
                f"Could not execute '{command}'"
            )

        if not path.isfile(pass1_filename):
            raise Albus_RINEX.No_RINEX_File_Error(
                "Pass 1 did not produce an output file"
            )

        # ---------- Pass 2 ----------
        command = (
            "gfzrnx -finp %s -fout %s "
            "-vo 2 -satsys G -obs_types 1,2 -chk "
            "-marker MK01"
            % (pass1_filename, final_tmp_filename)
        )
        if DEBUG_SET:
            print("clean_mk_rnx2: executing command", command)
        retcode = os.system(command)
        if retcode:
            raise Albus_RINEX.No_RINEX_File_Error(
                f"Could not execute '{command}'"
            )

        if not path.isfile(final_tmp_filename):
            raise Albus_RINEX.No_RINEX_File_Error(
                "Pass 2 did not produce an output file"
            )

        # ---------- remove original ----------
        command = "/bin/rm -rf " + in_filename
        if DEBUG_SET:
            print("clean_mk_rnx2: executing command", command)
        os.system(command)

        # ---------- move final into place ----------
        command = "mv %s %s" % (final_tmp_filename, final_output)
        if DEBUG_SET:
            print("clean_mk_rnx2: executing command", command)
        retcode = os.system(command)
        if retcode:
            raise Albus_RINEX.No_RINEX_File_Error(
                f"Could not execute '{command}'"
            )
        if DEBUG_SET:
            print("clean_mk_rnx2: cleaned file written to:", final_output)
        return final_output

    finally:
        # cleanup pass1
        if path.isfile(pass1_filename):
            command = "/bin/rm -rf " + pass1_filename
            if DEBUG_SET:
                print("clean_mk_rnx2: cleaning intermediate:", command)
            os.system(command)

        # cleanup leftover tmp
        if path.isfile(final_tmp_filename):
            command = "/bin/rm -rf " + final_tmp_filename
            if DEBUG_SET:
                print("clean_mk_rnx2: cleaning leftover tmp:", command)
            os.system(command)
        
        print(f"clean_mk_rnx2: {basename} converted to {final_basename}")