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