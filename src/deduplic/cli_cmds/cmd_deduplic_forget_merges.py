# import argparse
# from pathlib import Path
# from deduplic.core.merge_manager import forget_merges

# PROJECTS_DIR = Path(__file__).resolve().parents[2] / "projects"


# def main():
#     parser = argparse.ArgumentParser(
#         description="Deletes all pending merge drafts from the project's 'merges/' directory."
#     )
#     parser.add_argument(
#         "project_name",
#         type=str,
#         help="Name of the project located inside the 'projects/' directory."
#     )
#     # parser.add_argument(
#     #     "--confirm",
#     #     action="store_true",
#     #     help="Explicit confirmation required to delete the 'merges/' directory."
#     # )

#     args = parser.parse_args()

#     # if not args.confirm:
#     #     print("Error: Operation canceled. You must include the '--confirm' flag to discard all pending merge drafts.")
#     #     return

#     project_path = PROJECTS_DIR / args.project_name

#     if not project_path.exists():
#         print(f"Error: Project directory '{project_path}' does not exist.")
#         return

#     try:
#         forget_merges(project_path, confirm=True)
#     except Exception as e:
#         print(f"Error while discarding merge drafts: {e}")


# if __name__ == "__main__":
#     main()