# models/ — AI 模型權重與設定

## 子目錄

| 模型 | 用途 | 任務類型 |
|------|------|----------|
| [CanopySeg/](CanopySeg/) | 樹冠 / 植生 / 黃化 / 褐化分割 | Semantic segmentation (multi-class) |
| [LeafInst/](LeafInst/) | 葉片實例分割 + 尺度物偵測 | Instance segmentation + object detection |
| [LeafDefect/](LeafDefect/) | 病斑 / 黃化 / 壞死 / 破洞分割 | Semantic segmentation (multi-label) |

## 每個子目錄應包含

```
ModelName/
├── README.md           模型卡（Model Card）
├── config.yaml         訓練超參數與資料路徑
├── classes.json        類別定義
├── checkpoints/        訓練 checkpoint（gitignored）
├── exports/            推論用權重 ONNX / TorchScript（gitignored）
└── eval/               驗證報告（confusion matrix、IoU 等）
```

## 規範

- 權重檔（`.pt`、`.pth`、`.onnx`、`.safetensors`）已在 `.gitignore`
- 每次訓練須產生 Model Card（資料來源、訓練集大小、評估指標、已知限制）
- 版本號採 `v{MAJOR}.{MINOR}.{PATCH}` 對應 schema 變更等級
