"""What a deployable reads outside its own path (D148).

A component of the record is a deployable (D115), and the selection charges a change to the deployable it is under.
That holds only while the deployable reads nothing outside its own path, and a compiler, a type checker or a package
manager reaches another file in three ways, whatever the language: by a path, by another deployable's package or module
identity, or through a link. This reads those three over every file git lists under each deployable, tracked or
untracked and not ignored. Any reach is the full gate, with words that name the file, and so is any place the reader
cannot tell. No edge is charged to a unit, and no list of import syntaxes is kept.

`find` returns the words that follow `the full gate runs, as `make verify` — `, or None where nothing reaches out.
"""
from __future__ import annotations

import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

from .table import UNITS  # noqa: E402

ENDING = ("and the scoped gate scopes only a deployable that reads nothing outside its own path; share code through a "
          "package under `packages/` or a published contract to scope again")
QUOTED = re.compile(r"""["'`](\.\.[/\\][^"'`\n]*)["'`]""")
BARE = re.compile(r"""(?<![\w.])(\.\.[/\\][^\s"'`,;)\]}]*)""")
CONFIG = (".json", ".jsonc", ".toml", ".yaml", ".yml", ".xml", ".gradle", ".kts", ".cfg", ".ini", ".properties", ".mod",
          ".work", ".lock")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
PYTHON_FILES = re.compile(r"^(pyproject\.toml|uv\.lock|requirements[^/]*\.txt)$")
JAVA_FILES = re.compile(r"^(pom\.xml|[^/]*\.gradle|[^/]*\.gradle\.kts)$")
FAMILY_OF_IDENTITY = {"typescript": "npm", "go": "go", "python": "python", "java": "java"}


class Unsure(Exception):
    """The reader cannot tell what a deployable reads: the words say why, after `cannot be established: `, and
    `owner` is the path of the deployable that was being read."""

    def __init__(self, words: str, owner: str | None = None) -> None:
        super().__init__(words)
        self.owner = owner


def shown(text: str) -> str:
    return "".join(char if char.isprintable() else char.encode("unicode_escape").decode("ascii") for char in text)


def normal(name: str) -> str:
    """A Python distribution name as PEP 503 normalises it."""
    return re.sub(r"[-_.]+", "-", name).lower()


def git_bytes(root: Path, *args: str) -> bytes | None:
    try:
        done = subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError:
        return None
    return done.stdout if done.returncode == 0 else None


def listed(root: Path, paths: list[str]) -> tuple[dict[str, list[str]], set[str]]:
    """The files git lists under each path, tracked or untracked and not ignored, from one listing of the tree, and the
    links among the ignored ones: a link is read whether or not git ignores it. A file that is gone from the working
    tree is not there to read."""
    out = git_bytes(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if out is None:
        raise Unsure("git cannot list the tree", paths[0] if paths else None)
    hidden = git_bytes(root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard")
    if hidden is None:
        raise Unsure("git cannot list the ignored files", paths[0] if paths else None)
    names = sorted({name.decode("utf-8", "surrogateescape") for name in out.split(b"\0") if name})
    links = {name for name in (item.decode("utf-8", "surrogateescape") for item in hidden.split(b"\0") if item)
             if any(inside(name, path) for path in paths) and (root / name).is_symlink()}
    every = sorted(set(names) | links)
    found = {path: [name for name in every if inside(name, path) and name != path
                    and ((root / name).is_symlink() or (root / name).exists())] for path in paths}
    return found, links


def text_of(data: bytes | None) -> str:
    return "" if data is None else data.decode("utf-8", "replace")


def identity(family: str, manifest: str) -> set[str]:
    """The names a deployable of `family` answers to, from its manifest's text; empty where there is none."""
    found: set[str] = set()
    if family == "typescript":
        try:
            name = json.loads(manifest).get("name")
        except (ValueError, AttributeError):
            name = None
        found.add(name) if isinstance(name, str) and name else None
    elif family == "go":
        match = re.search(r"^module\s+(\S+)", manifest, re.M)
        found.add(match.group(1).strip('"')) if match else None
    elif family == "python":
        section = re.search(r"^\[project\]\s*$(.*?)(?=^\[|\Z)", manifest, re.M | re.S)
        match = re.search(r"""^name\s*=\s*["']([^"']+)["']""", section.group(1), re.M) if section else None
        found.add(normal(match.group(1))) if match else None
    elif family == "java":
        match = re.search(r"<artifactId>([^<$]+)</artifactId>", re.sub(r"<parent>.*?</parent>", "", manifest, flags=re.S))
        found.add(match.group(1).strip()) if match else None
    return found


MANIFEST = {"typescript": "package.json", "go": "go.mod", "python": "pyproject.toml", "java": "pom.xml"}


def at_base(root: Path, base: str | None, paths: list[str]) -> dict[str, str]:
    """The text of each path at the base that is there, from one `git cat-file --batch` whose input names them."""
    if base is None:
        return {}
    request = "".join(f"{base}:{path}\n" for path in paths).encode("utf-8", "surrogateescape")
    try:
        done = subprocess.run(["git", "cat-file", "--batch"], cwd=root, input=request, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=False)
    except OSError:
        return {}
    found: dict[str, str] = {}
    out, at = done.stdout, 0
    for path in paths:
        end = out.find(b"\n", at)
        if done.returncode != 0 or end < 0:
            break
        header = out[at:end].split()
        at = end + 1
        if len(header) == 3 and header[1] == b"blob":
            size = int(header[2])
            found[path] = text_of(out[at:at + size])
            at += size + 1
    return found


def identities(root: Path, deployables: dict[str, dict[str, Any]], base: str | None) -> dict[str, set[str]]:
    """Each deployable's identity, from its manifest in the working tree and at the base, the two together: a branch
    that renames one still finds a reference to the old name."""
    manifests = {name: f"{item['path']}/{MANIFEST[item['family']]}" for name, item in deployables.items()
                 if item["family"] in MANIFEST}
    before = at_base(root, base, list(manifests.values()))
    found: dict[str, set[str]] = {}
    for name, item in deployables.items():
        found[name] = set()
        if name not in manifests:
            continue
        here = root / manifests[name]
        texts = [text_of(here.read_bytes()) if here.is_file() else "", before.get(manifests[name], "")]
        found[name] = set().union(*(identity(item["family"], text) for text in texts))
        if not found[name]:
            raise Unsure(f"the identity of the deployable `{name}` cannot be read from `{shown(manifests[name])}` in "
                         "the tree or at the base", item["path"])
    return found


def inside(path: str, directory: str) -> bool:
    return path == directory or path.startswith(directory + "/")


def exempt(path: str, item: dict[str, Any], packages: list[str]) -> bool:
    """A target that is one of the deployable's own row file inputs, or a package it consumes as a contract."""
    own = [entry for entry in UNITS.get(item["family"], UNITS["typescript"]).files if not entry.startswith("{")]
    if path in own:
        return True
    return item["family"] == "typescript" and any(inside(path, f"packages/{package}") for package in packages)


class Readers:
    """The patterns one scan reads every file with, each compiled once over every deployable: one for the paths of the
    deployables and one per family for their identities, so a file is read in one pass however many deployables there
    are."""

    def __init__(self, deployables: dict[str, dict[str, Any]], names: dict[str, set[str]]) -> None:
        self.owners: dict[str, set[str]] = {}
        for name, known in names.items():
            for identity_name in known:
                self.owners.setdefault(identity_name, set()).add(name)
        self.paths: dict[str, set[str]] = {}
        for name, item in deployables.items():
            self.paths.setdefault(str(item["path"]), set()).add(name)
        self.path_pattern = self.combined(sorted(self.paths), r"(?<![\w/.-])", r"(?![\w-])")
        around = {"typescript": (r"(?<![\w@./-])", r"(?![\w-])"), "go": (r"(?<![\w./-])", r"(?![\w.-])"),
                  "java": (r"(?<![\w.-])", r"(?![\w.-])")}
        self.identity_pattern = {family: self.combined(sorted(self.owners), *edges) for family, edges in around.items()}

    @staticmethod
    def combined(words: list[str], before: str, after: str) -> re.Pattern[str] | None:
        if not words:
            return None
        return re.compile(before + "(" + "|".join(re.escape(word) for word in sorted(words, key=lambda w: (-len(w), w)))
                          + ")" + after)

    def other(self, pattern: re.Pattern[str] | None, text: str, table: dict[str, set[str]], name: str) -> tuple[str, str] | None:
        """(the word found, the first other deployable that holds it) for the first match in `text` of a word that
        some deployable other than `name` holds."""
        for match in pattern.finditer(text) if pattern else ():
            others = sorted(table[match.group(1)] - {name})
            if others:
                return match.group(1), others[0]
        return None


def path_reach(file: str, text: str, name: str, deployables: dict[str, dict[str, Any]], packages: list[str],
               readers: Readers) -> str | None:
    """The first target outside the deployable that a path in this file lands on, or None. A path in a manifest or a
    config is read against the deployable's root as well as its own directory."""
    item = deployables[name]
    config = file.endswith(CONFIG) or file.rsplit("/", 1)[-1].startswith("requirements")
    patterns = (QUOTED, BARE) if config else (QUOTED,)
    directories = [posixpath.dirname(file)] + ([item["path"]] if config else [])
    for pattern in patterns:
        for match in pattern.finditer(text):
            for directory in directories:
                landed = posixpath.normpath(posixpath.join(directory, match.group(1).replace("\\", "/")))
                if landed == ".." or landed.startswith("../"):
                    raise Unsure(f"`{shown(file)}` climbs above the repository root")
                if not inside(landed, item["path"]) and not exempt(landed, item, packages):
                    return landed
    found = readers.other(readers.path_pattern, text, readers.paths, name)
    return found[0] if found else None


def identity_reach(file: str, text: str, name: str, deployables: dict[str, dict[str, Any]],
                   readers: Readers) -> tuple[str, str] | None:
    """(the name found, the deployable it is the package of) for the first identity of another deployable that this
    file names, where a resolver of this file's family would resolve it without a declaration."""
    family = deployables[name]["family"]
    base = file.rsplit("/", 1)[-1]
    if family == "python":
        if not PYTHON_FILES.match(base):
            return None
        for token in TOKEN.findall(text):
            owners = readers.owners.get(normal(token), set()) - {name}
            if owners:
                return token, sorted(owners)[0]
        return None
    if family == "java" and not JAVA_FILES.match(base):
        return None
    found = readers.other(readers.identity_pattern.get(family), text, readers.owners, name)
    return found


def link_reach(root: Path, file: str, directory: str, ignored: bool = False) -> str | None:
    real_root, real_directory = (Path(p).resolve() for p in (root, root / directory))
    try:
        target = (root / file).resolve()
    except (OSError, RuntimeError) as error:
        raise Unsure(f"the link `{shown(file)}` cannot be resolved ({type(error).__name__})") from error
    if target == real_directory or real_directory in target.parents:
        return None
    try:
        return target.relative_to(real_root).as_posix()
    except ValueError as error:
        if ignored:  # a file git ignores that leads out of the repository (a `.venv`'s interpreter) reads none of it
            return None
        raise Unsure(f"the link `{shown(file)}` leads outside the repository") from error


def scan(root: Path, deployables: dict[str, dict[str, Any]], packages: list[str], base: str | None) -> str | None:
    names = identities(root, deployables, base) if len(deployables) > 1 else {name: set() for name in deployables}
    files, ignored = listed(root, [str(item["path"]) for item in deployables.values()])
    readers = Readers(deployables, names)
    for name, item in deployables.items():
        try:
            found = scan_one(root, name, deployables, packages, names, files[item["path"]], ignored, readers)
        except Unsure as error:
            raise Unsure(str(error), error.owner or item["path"]) from error
        if found is not None:
            return found
    return None


def scan_one(root: Path, name: str, deployables: dict[str, dict[str, Any]], packages: list[str],
             names: dict[str, set[str]], files: list[str], ignored: set[str],
             readers: Readers) -> str | None:
    directory = deployables[name]["path"]
    for file in files:
        here = f"`{shown(file)}`"
        outside = f"outside its deployable `{shown(directory)}`, {ENDING}"
        if (root / file).is_symlink():
            target = link_reach(root, file, directory, file in ignored)
            if target is not None:
                return f"{here} reaches `{shown(target)}`, {outside}"
            continue
        try:
            text = text_of((root / file).read_bytes())
        except OSError as error:
            raise Unsure(f"cannot read `{shown(file)}` ({error.strerror or type(error).__name__})") from error
        landed = path_reach(file, text, name, deployables, packages, readers)
        if landed is not None:
            if not (root / landed).exists() and not (root / landed).is_symlink() and not any(
                    inside(landed, str(item["path"])) for item in deployables.values()):
                return (f"{here} holds a string that climbs out of `{shown(directory)}` onto `{shown(landed)}`, "
                        f"which is no deployable and no path in the repository, {ENDING}")
            return f"{here} reaches `{shown(landed)}`, {outside}"
        named = identity_reach(file, text, name, deployables, readers)
        if named is not None:
            return f"{here} names `{shown(named[0])}`, the package of the deployable `{shown(named[1])}`, {outside}"
    return None


def find(root: Path, deployables: dict[str, dict[str, Any]], packages: list[str], base: str | None) -> str | None:
    """The words saying that a deployable reads outside its own path, or that what it reads cannot be established; None
    where every deployable reads nothing outside its own path."""
    try:
        return scan(root, deployables, packages, base)
    except Unsure as error:
        return f"what `{shown(error.owner or 'a deployable')}` reads outside its path cannot be established: {error}"
