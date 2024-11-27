# GenomeChat-TestApp

![Screenshot_1](https://github.com/user-attachments/assets/5a3dae12-349b-4273-9992-e3b5010219a2)

GenomeChat is a chatbot able to perform analysis on genomic annotations. It generates python code using the gffutils library and the runs the analysis script on background. According to the user's query, GenomeChat will generate, run and explain the analysis scripts and results.

This is a test application under development available for GenomeChat, based on the Large Language Model [Qwen2.5 7B](https://qwenlm.github.io/blog/qwen2.5/) pulled from [Ollama](https://ollama.com/library/qwen2.5:7b). The streamlit app was developed during my masters' classes on Machine Learning and Pattern Recognition. Unfortunately, the data and model are too heavy to run on streamlit site online, so I had to test it under my local environment.

I am leaving it available, but the prompt is hidden on a secrets.toml file. So you feel free to create and test your own prompts for the application.

I am a newbie to streamlit, so I still could not fix the problems to display dataframes and plot figures in the chat. If you ever fix it, please make a pull request :)

**Obs: this is a tool in tests and initial development, feel free to give me any applicable suggestions!**

## Instructions

1. When using GenomeChat on your local machine, you can either upload a .gff, gff3 or .gtf file for conversion to database (.db) or input an already processed .db file.
2. Depending on your machine's configurations, uploading a raw annotation file can take long, specially if you are using a remote (tunnel or ssh) connection. So it can be better to use a local .db file.
3. You can store your secret prompt under a secrets.toml file in the .streamlit folder. 

## Annotation files used for the tests

For the tests executed, we used the Human annotation from Ensembl databes (under release 112).
You can find the files (.gtf and .db) I used for tests in my Drive: https://drive.google.com/drive/folders/1Ftez3EWK3DNs_6Mtxi82Bl9UtB8IBQpY?usp=sharing

## Minimal computational requirements

The tests were performed on a machine with the following configurations:
• CPU: Intel(R) Core(TM) i7-10700 @ 2.90GHz;
• GPU: GeForce RTX 2060 SUPER;
• RAM: 16 GB. 

## Important notes

The application was developed and used only for scientific knowledge and research purposes. Commercial use is not allowed.

If you have any doubts, contact me by email: mbarborgess@gmail.com
