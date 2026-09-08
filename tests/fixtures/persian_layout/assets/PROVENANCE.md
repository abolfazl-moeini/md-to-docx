# Asset Provenance & License Notice

This directory contains test assets used for Persian layout rendering and regression tests (S09, F00, F17).

## Asset Manifest

| Filename | Type / Dimensions | Source & Creation | License | SHA-256 |
| :--- | :--- | :--- | :--- | :--- |
| `photo_horizontal.png` | PNG, 1280×720 | Original test photograph generated 2026-09-07 for this repository (server-room scene). Not a crop of `sample-template/`. | Original test asset; not a third-party photo. Do not treat as CC0. | `7ec9a9755d4c482f6b5d866e2ac92846ab3caba350b759dc514b9732243bd01e` |
| `photo_vertical.png` | PNG, 832×1248 | Original test photograph generated 2026-09-07 for this repository (open rack, portrait). Not a crop of `sample-template/`. | Original test asset; not a third-party photo. Do not treat as CC0. | `59c002d95cad8edc2ef5b2d910b27ee68c179802b8d278aeeb0c2d1493e15158` |
| `tiny_inline.png` | PNG, 32×18 | Downscaled derivative of `photo_horizontal.png` for inline-image tests. | Same as parent asset. | `70555b14c6d05b5cacadacde9111d6923948515035cc5333aaaa89cc3abb48e7` |
| `horizontal_sample.png` | PNG, 800×400 | Synthetic technical diagram created for layout tests (SQL architecture labels). | Original test diagram. | `b04ad9690a274c6b90fa9da9e269e09a72b9804577b04ac7cb7d291b7e690c6b` |
| `vertical_sample.png` | PNG, 400×700 | Synthetic technical diagram created for layout tests (storage hierarchy). | Original test diagram. | `e93a5e0395682ae69c231d78fda2880f8c7d68b8095c4b728bbc813b7305b9b2` |
| `transparent_sample.png` | PNG RGBA, 500×250 | Synthetic alpha badge created for layout tests. | Original test diagram. | `44a7567b8adad4481bb2dbdb2eda415e30f1f570c1a5bd5387939d57bf4735c9` |
| `sample with spaces.png` | PNG, 400×200 | Crop of project visual reference `sample-template/1.jpg` used only as a filename/spaces fixture. **Not** a real photograph and **not** a CC0 work. | Project reference crop; license follows the sample-template source, not CC0. | `dcef9251041b76854628c9a07a57d09b5574cfd73c295fb76ab88aacc6e590a6` |
| `تصویر_نمونه_فارسی.png` | PNG, 450×220 | Synthetic technical diagram with Persian labels. | Original test diagram. | `69aa1787aa19cebfe0dc784e982c8b109f5581cca54dfc7c6359f4f842840ab5` |
| `logo.png` | PNG RGBA, 64×64 | Geometric emblem created for header/logo tests. | Original test diagram. | `036e2a3707d146874ade06aee051d00fd4daa19b5b6348b10692017368d0bc4a` |

Hashes should be re-verified with `shasum -a 256` if an asset is regenerated.
