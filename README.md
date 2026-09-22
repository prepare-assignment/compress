# Compress action

Compress files into an archive. For now only zip-archives are supported.

## Options

The following options are available:

```yaml
inputs:
  description: "Glob(s) to files/directories to compress"
  required: true
  type: array
  items: string
excluded:
  description: "Glob(s) to exclude from matching the inputs"
  required: false
  type: array
  items: string
output:
  description: "The output path"
  required: true
working-directory:
  description: "Set a different working directory, the glob(s) will be matched from this new pwd"
  required: false
allow-outside-working-directory:
  description: "Allow the glob(s) to match outside the working directory (outside means up the working tree)"
  required: false
  default: false
recursive:
  description: "Recursively match files in directories"
  type: boolean
  default: true
```

## Outputs

The following output are available:

```yaml
files:
  description: The files added to the archive
  type: array
  items: string
```

## Releases

Releases are automated with [semantic-release](https://semantic-release.gitbook.io/). Pull requests are squash merged, so the PR title becomes the commit on `main` and must follow [Conventional Commits](https://www.conventionalcommits.org/) (checked on every PR):

| PR title | Release |
|----------|---------|
| `fix: ...`, `perf: ...` | patch (1.2.3 → 1.2.4) |
| `feat: ...` | minor (1.2.3 → 1.3.0) |
| `!` after the type (e.g. `feat!: ...`, `refactor!: ...`) or a `BREAKING CHANGE:` footer | major (1.2.3 → 2.0.0) |
| `docs:`, `chore:`, `ci:`, `build:`, `refactor:`, `test:`, `style:`, `revert:` | no release |

On every merge to `main` the next version is determined, tagged (`vX.Y.Z`) and a GitHub release is created. The major tag (e.g. `v1`) is moved to the new release, so `uses: compress@v1` always gets the newest 1.x version.
