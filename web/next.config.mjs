// ONIZLEME_ONEK sadece JupyterLab önizlemesi için (/lab/proxy/7860); Vercel'de boş kalır.
const onek = process.env.ONIZLEME_ONEK;
export default onek ? { assetPrefix: onek } : {};
