# MobileNet-SSD Model Files

This directory must contain two files before running the system:

## Required Files

| File | Size | Description |
|------|------|-------------|
| `MobileNetSSD_deploy.prototxt` | ~30 KB | Network architecture definition |
| `MobileNetSSD_deploy.caffemodel` | ~23 MB | Pre-trained weights (PASCAL VOC) |

## Download Instructions

### Option 1 — curl (macOS)

macOS does not have `wget` installed by default. Use `curl`:

```bash
cd model/

# Download the .prototxt (network architecture)
curl -O https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/deploy.prototxt

# Download the .caffemodel (pre-trained weights — ~23 MB)
# Note the -L flag to follow GitHub redirects
curl -O -L https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/mobilenet_iter_73000.caffemodel
```

### Option 2 — wget (Raspberry Pi / Linux)

```bash
cd model/

# Download the .prototxt
wget https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/deploy.prototxt

# Download the .caffemodel
wget https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/mobilenet_iter_73000.caffemodel
```

## Verification

After downloading, confirm the files are in place:

```bash
ls -lh model/
# Expected output:
# MobileNetSSD_deploy.caffemodel   (~23 MB)
# MobileNetSSD_deploy.prototxt     (~44 KB)
```

## Supported Vehicle Classes

MobileNet-SSD is trained on PASCAL VOC (21 classes). The system filters
for these vehicle-related class IDs:

| Class ID | Label      |
|----------|------------|
| 6        | bus        |
| 7        | car        |
| 14       | motorbike  |

You can add more classes (e.g., `15` = person) in `config.py` → `VEHICLE_CLASS_IDS`.
