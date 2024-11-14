import { formData, zfd } from "zod-form-data";


const schema = zfd.formData({
	input: zfd.file(),  
});

export async function POST(request: Request) {
	// console.time("transcribe " + request.headers.get("x-vercel-id") || "local");

	const { data, success } = schema.safeParse(await request.formData());
	if (!success) return new Response("Invalid request", { status: 400 });

	const transcript = await getTranscript(data.input);
	if (!transcript) return new Response("Invalid audio", { status: 400 });



	// Return the transcription only
	return new Response(transcript, {
		headers: { "Content-Type": "text/plain" },
	});
}


async function getTranscript(input: string | File) {
	if (typeof input === "string") return input;

	try {
        const formData = new FormData();
        formData.append("input", input, "audio.mp3");
		const response = await fetch("http://localhost:8000/stt", {
			method: "POST",
			body: formData,
		});
        const text = await response.text();

		return text || null;
	} catch {
		return null; // Empty audio file
	}
}