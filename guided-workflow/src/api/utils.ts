export const compressData = async (data: unknown): Promise<Blob> => {
  const jsonString = JSON.stringify(data);
  const encoder = new TextEncoder();
  const encodedData = encoder.encode(jsonString);

  const compressionStream = new CompressionStream("gzip");
  const compressedStream = new Blob([encodedData])
    .stream()
    .pipeThrough(compressionStream);
  return await new Response(compressedStream).blob();
};
