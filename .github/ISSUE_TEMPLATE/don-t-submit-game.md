---
name: don't Submit Game
about: Submit a request to add your game!
title: ''
labels: needs approval, publish this game plz
assignees: ''

---

name: don't Submit Game
description: Submit a request to add your game!
title: "[New Game] <Game Name>"

labels: ["publish this game plz", "needs approval"]

body:
- type: input
  id: id
  attributes:
    label: Game ID (e.g., io.github.amnoshield.RecycledCybernetics)
  validations:
    required: true

- type: input
  id: file_name
  attributes:
    label: File name (ie. Recycled_Cybernetics_linux.x86_64)
  validations:
    required: true

- type: input
  id: source_url
  attributes:
    label: Github release tarball URL
  validations:
    required: true

- type: input
  id: sha256
  attributes:
    label: SHA256 of source
  validations:
    required: true
