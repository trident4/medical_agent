from moviepy import VideoFileClip, concatenate_videoclips, vfx

def create_demo_reel(input_file, output_file):
    print("Loading video... this might take a minute.")
    video = VideoFileClip(input_file)

    # --- CLIP 1: INTRO & PATIENT LOOKUP (Speed up typing) ---
    # 00:00 to 00:04 (Login & List)
    intro = video.subclipped(0, 4)
    
    # 00:10 to 00:22 (Asking about John's last visit)
    # We speed up the typing part (00:10 to 00:18)
    typing_1 = video.subclipped(10, 18).with_effects([vfx.MultiplySpeed(2.0)]) # 2x speed
    result_1 = video.subclipped(18, 22) # Normal speed for reading result

    # --- CLIP 2: VISUAL ANALYTICS (The Pie Chart) ---
    # 00:30 to 00:42 (Asking for chart + result)
    typing_2 = video.subclipped(30, 39).with_effects([vfx.MultiplySpeed(2.0)])
    result_2 = video.subclipped(39, 44) # Show the chart longer

    # --- CLIP 3: CLINICAL REASONING (The "Wow" factor) ---
    # 00:55 to 01:05 (Asking about main problem/hypertension)
    typing_3 = video.subclipped(55, 59).with_effects([vfx.MultiplySpeed(2.0)])
    result_3 = video.subclipped(59, 105)

    # --- CLIP 4: ANALYTICS & SQL (The Tech Flex) ---
    # 02:30 to 02:42 (Asking about visits in last 34 days + Showing SQL)
    typing_4 = video.subclipped(150, 153).with_effects([vfx.MultiplySpeed(2.0)]) # "Which patient has most visits"
    result_4 = video.subclipped(153, 158)
    
    # The SQL query reveal (Crucial for devs)
    sql_reveal = video.subclipped(156, 163) 

    # --- COMBINE ---
    final_clip = concatenate_videoclips([
        intro, 
        typing_1, result_1, 
        typing_2, result_2, 
        typing_3, result_3,
        typing_4, result_4,
        sql_reveal
    ], method="compose")

    # Write the file
    print("Rendering final video...")
    final_clip.write_videofile(output_file, codec='libx264', audio_codec='aac')
    print(f"Done! Saved as {output_file}")

# Run the function
if __name__ == "__main__":
    create_demo_reel("Medical Agent Demo.mov", "LinkedIn_Final_Cut.mp4")