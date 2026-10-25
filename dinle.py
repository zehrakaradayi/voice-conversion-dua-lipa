"""Ara dinleme sayfası: Model A'yı orijinal ve Öğretmen ile karşılaştır.

    ROOT_PATH=/lab/proxy/7861 .venv/bin/python dinle.py
"""
import os

import gradio as gr

O = "outputs/asama4"
with gr.Blocks(title="Model A ve B dinleme") as demo:
    gr.Markdown("## Dua Lipa sesiyle *Üzülmedin mi*: Model A ve B\nSadece vokal (enstrüman yok). Yapay zekâ ile üretilmiştir.")
    gr.Audio("dataset_temiz/ref/seedvc_ref.wav", label="Referans: Dua Lipa'nın gerçek sesi", interactive=False)
    gr.Markdown("### İlk kıta, 10 sn")
    with gr.Row():
        gr.Audio(f"{O}/hedef_kita.wav", label="Orijinal: Simge", interactive=False)
        gr.Audio(f"{O}/A_kita_115e.wav", label="Model A (sadece gerçek)", interactive=False)
        gr.Audio(f"{O}/B_kita_77e.wav", label="Model B (gerçek + sentetik)", interactive=False)
    gr.Markdown("### Şarkının tamamı")
    gr.Audio("stems/cover_simge_uzulmedin_mi_lead.wav", label="Orijinal: Simge", interactive=False)
    gr.Audio(f"{O}/cover_simge_uzulmedin_mi_A_115e.wav", label="Model A (sadece gerçek) · Ses benzerliği %72.7 · oktav %95.4", interactive=False)
    gr.Audio(f"{O}/cover_simge_uzulmedin_mi_B_77e.wav", label="Model B (gerçek + ayıklanmamış sentetik) · Ses benzerliği %63.4 · oktav %95.4", interactive=False)
    gr.Audio("teacher/cover_simge_uzulmedin_mi.wav", label="Öğretmen (Seed-VC, eğitimsiz) · Ses benzerliği %46.8", interactive=False)
demo.launch(server_name="0.0.0.0", server_port=7861, root_path=os.environ.get("ROOT_PATH", ""),
            allowed_paths=[os.path.abspath(p) for p in (O, "dataset_temiz/ref", "stems", "teacher")])
