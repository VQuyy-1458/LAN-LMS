import { BrowserQRCodeReader } from "@zxing/browser";
// Decode photographs at bounded resolutions instead of feeding a multi-megapixel
// image directly to ZXing. Camera EXIF orientation is applied by the browser.
export async function decodeQrImage(file: File): Promise<string> {
  const url=URL.createObjectURL(file), image=new Image();
  try {
    image.src=url; await image.decode();
    const NativeDetector=(window as unknown as {BarcodeDetector?:new(options:{formats:string[]})=>{detect:(image:HTMLImageElement)=>Promise<{rawValue:string}[]>}}).BarcodeDetector;
    if(NativeDetector) {
      try{const found=await new NativeDetector({formats:["qr_code"]}).detect(image);if(found[0]?.rawValue)return found[0].rawValue}catch{/* Use the bundled decoder when the native API cannot read this photo. */}
    }
    const reader=new BrowserQRCodeReader();
    for (const max of [1200,800,1800]) {
      const ratio=Math.min(1,max/Math.max(image.naturalWidth,image.naturalHeight));
      const w=Math.max(1,Math.round(image.naturalWidth*ratio)),h=Math.max(1,Math.round(image.naturalHeight*ratio));
      for (const angle of [0,90,180,270]) {
        const canvas=document.createElement("canvas");
        canvas.width=angle%180?h:w;canvas.height=angle%180?w:h;
        const ctx=canvas.getContext("2d",{willReadFrequently:true});
        if (!ctx) throw new Error("Không tạo được vùng đọc ảnh");
        ctx.fillStyle="#fff";ctx.fillRect(0,0,canvas.width,canvas.height);
        ctx.translate(canvas.width/2,canvas.height/2);ctx.rotate(angle*Math.PI/180);ctx.drawImage(image,-w/2,-h/2,w,h);
        try {return reader.decodeFromCanvas(canvas).getText()} catch { /* Try another orientation/contrast. */ }
        const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);
        for(let i=0;i<pixels.data.length;i+=4){
          const luminance=.299*pixels.data[i]+.587*pixels.data[i+1]+.114*pixels.data[i+2];
          const contrast=Math.max(0,Math.min(255,(luminance-128)*1.7+128));
          pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=contrast;
        }
        ctx.putImageData(pixels,0,0);
        try {return reader.decodeFromCanvas(canvas).getText()} catch { /* Next attempt. */ }
        await new Promise<void>(resolve=>setTimeout(resolve,0));
      }
    }
    throw new Error("Không đọc được mã QR. Hãy chụp gần hơn, giữ đủ bốn góc và tránh phản sáng trên màn hình.");
  } finally {URL.revokeObjectURL(url)}
}
