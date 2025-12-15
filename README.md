# Geo-Synchronized Audio Reannotation and Semantic Search for SVG Analysis
Chosen journal: Nature Scientific Reports
## Abstract

Spatial video geonarratives (SVGs) combine the power of geosynced-video data with expert in-field commentary to uncover features and insights that are difficult capture via other methods of data collection. Current SVG workflows require a large amount of manual labor and data post-processing before analysis to begin. While interfaces have been created to mitigate this problem, there has been no development in the workflow for annotation pre-existing spatial videos (SVs) or SVGs. Thus current workflows limit the scalability and accessibility of this dataset for GIS and non-GIS users alike. This paper provides a prototype interface designed to automatically handle the manual labor and post-processing, so the workflow gets simplified down to natural actions such as watching and speaking. Another challenge for SVGs exists in the retrieval of specific data from transcripts. Current methodology utilizes keyword search, that retrieves based off exact text-matching, limiting the data that can be retrieved and causing loss of data. This paper implements semantic search to introduce meaning-based search, solving the issue of keyword search's strict retrieval criteria. Thus the new proposed interface provides an enhanced method of data collection and analysis for SVG data.


## 1. Introduction

In recent times, spatial videos (SV) has been an invaluable data source in the field of public health by pairing detailed visual information with geographical information. The combination of GPS data and video provides researches the ability to map street-level phenomena not easily captured via other methods. By including expert in-field commentary, spatial video geonarratives (SVG) are created, providing rich insights to visual observations [3]. SVs and SVGs have been used by researchers in the past to investigate various public health concerns including investigating neighborhood dynamics, environmental risks, or healthcare risks/access [4]. 

Even though these data types have been used widely for many years, existing workflows to process this data still require manual post-processing. After video collection, researches must (1) review the video, (2) transcribe the audio, (3) manually align the audio to GPS data, (4) match time formats between GPS data and audio data, (5) and imported to any GIS software for mapping [4]. While new advancements have been made with new interfaces/softwares such as Wordmapper to generate the base SVGs, these methods still do not provide a method to easily add additional annotations without having to resort to manual file manipulation [1].

Another challenge that exists in the manipulation of SVG data involves the process of efficiently retrieving insights within the narrative transcripts. Current ways to filter through the transcript offered by software such as ArcGIS Pro is based off keyword search. Keyword searches are unable to capture the user intent and context from a query, resulting in requiring multiple searches that may still result in loss of data if all relevant keywords were not used. Semantic search address this issue by providing a more powerful method by searching through meaning and context. Previous work has been done in implementing semantic search to on geoportals such as ArcGIS Online to find and uncover spatial datasets that match the meaning of user queries [6]. Researchers discovered that their semantic search algorithm outperformed ArcGIS Online's implementation Lucene search, a form of keyword search. There has been no previous implementation of semantic search for SVG data, indicating a gap within current methodologies.

Thus, to address both problems, I present a prototype interface for Geo-Synchronized Audio Re-Annotation and Semantic Search Analysis tailored to SVG. My system allows users to add new spoken commentary to any spatial video with automatic GPS alignment based on the current video timestamp. This eliminates any need to manually create/manipulate data files or any manual marker placements. Newly added audio can instantly be plotted on the system's interactive map or the data can be exported to more specialized GIS software. The interface also embeds the original transcript and user queries, allowing users retrieve similarity data within the embedding vector space and perform meaning-based search rather than strictly text-based search. This combination of automated spatial annotation and meaning-based data retrieval increases accessibility, enhances scalability, and provides a framework for future multi-expert collaborations, allowing the creation of richer, multi-perspective SVG dataset.


## 2. Background and Related Works

Prior studies have demonstrated that street-level imagery and video have been vital resources for auditing built environment features, including sidewalks, land use, and neighborhood conditions [2,7] through tools such as Google Street View. These studies demonstrate the usefulness that geo-referenced visual data have in analyzing local environments as well as the benefits of reducing logistical burden that results from requiring repeated on-location visits. Complementary work using machine learning technique to analyze large collections of street-level imagery to predict human perceptions of street-view imagery  [11]. Despite these advancements, no these studies incorporate spoken narrative or audio commentary as a data source. Studies that do contain narrative data highlight the manual labor and post-processing required to analyze said data with no alternative workflow for adding new data [1,4]. As a result, the workflow for adding additional narrative data still remains mainly manual and requires sufficient GIS background experience to perform.

Recent advancements in Natural Language Processing (NLP) have resulted in widespread adoption and development of semantic search. Vector embeddings of data allow the retrieval of contextually similar data with transformer-based models such as BERT and Sentence-BERT demonstrating strong performance in performing these such tasks [5,8]. This method of search has been widely adopted in many differing domains to improve search functions.

Within the GIS domain, semantic search has been explored in searching for datasets on geoportals such as ArcGIS Online [6]. The performance of the semantic search function was compared to the performance of the ArcGIS Online's currently utilized Lucene search, a form of keyword. The study discovered that the semantic search function beat Lucene search in data retrieval indicating the usefulness that semantic search has within the GIS domain. Semantic search has also applied to analyze Instagram social media posts to capture distinct semantic profiles to the different city districts of Bonn, Germany [10]. The GPS location that was tied to each post was used to determine the location of posts with best results, allowing mapping of differing perceptions of the area. While many of applications exist for semantic, no study has implemented its use in analyzing audio-transcribed data or spatiotemporally synchronized narrative data. Specifically, no semantic search function has ever been implemented in the analysis of SVG data where both time and location are of importance. This gap highlights the motivation for semantic search functions to be developed directly for the analysis of geo-synchronized audio transcripts within SVG pipelines.


## 3. Method

### 3.1 Data Acquisition

SVG data describing the air quality conditions around Newburgh Heights, Ohio was acquired from the GIS Health & Hazards Lab (GHHL). The dataset consists of 1.1 hours of dash-mounted video collected during a mobile survey of the neighborhood with in-field commentary provided by local experts. GPS coordinates associated with the video was provided in CSV format with columns containing video timestamps, latitude, and longitude data. The transcribed narrative were also provided in CSV format with columns including start times and end times (in seconds) alongside the corresponding text. For performance evaluations, additional audio was recorded with the default computer microphone.


### 3.2 Geo-Synchronized Audio ReAnnotation Pipeline


![[Pasted image 20251212222236.webp|559]]

![[Screenshot 2025-12-13 at 3.15.22 AM.webp|562]]


The re-annotation pipeline integrates GPS data, video timestamps, user-generated audio, and database storage to create new geo-linked narrative observations. The main interface for this pipeline was built using the Panel python library and can be seen in Figure 1.

#### 3.2.1 Data Loading

Users begin by first providing all the necessary CSV data files in the same folder directory as the python file “app.py” and changing the file names within “app.py” to their correct corresponding file names. Users must then host the video data through an Apache webserver and reference that web address within “app.py”.

#### 3.2.2 Video-GPS Syncing

Once all the data has been properly provided, the interface then extracts the current time of the video to the nearest second and match the video time to its corresponding GPS data. The GPS data is then plotted on the interactive map as a single point and displayed as the current position. As the video plays, this point will move with the accordance to the video. The transcript data is displayed as a table with start time data being converted to a timestamp format. Users then can perform keyword search and plot the results on the map as well.

#### 3.2.3 Audio Recording and ReAnnotation

While watching the video, users can pause the video and record new audio commentary via the interface. They will then be able to replay the audio and save it. The audio file is saved temporarily in WAV format and will get replaced upon subsequent recordings. If the user chooses to save the audio, the temporarily WAV file will be converted to WAV bytes. The audio then gets transcribed using OpenAI’s Whisper library and the video timestamp is recorded. Timestamp, transcript, and WAV bytes data are then given a designated ID and stored into a table named Recordings in a vector database that was implemented using Postgres. This database is reflected and displayed as a table by the interface with columns for ID, timestamp, and transcript. Once saved, users can retrieve the saved audio by ID and play it back. Users can also search the database through the interface and plot any results onto the on-screen map or export the results as an CSV file. The columns in the exported CSV file are the same as displayed on the table. The location data for the new audio is determined by linking the audio timestamp with the timestamps from the GPS data. An example of the exporting to ArcGIS is shown below:

![[Screenshot 2025-12-13 at 3.14.06 AM.webp]]

### 3.3 Semantic Search Pipeline

The semantic search portion of the pipeline aims to provide users the ability to search for similar meanings and contexts to the user query within the transcript.

#### 3.3.1 Transcript Embedding

Users are presented with a new copy of the transcript table with a text input for users to enter their query. All the text within the transcript is embedded using the all-MiniLM-L6-v2 Sentence Transformer model, and the resulting embeddings are stored along with the video time in seconds, and the transcript text within the Embedding table in the vector database. 

#### 3.3.2 Expanding Queries

Once users enter their query, the query is also embedded, and cosine similarity was run to create raw accuracy scores. To produce more accurate results, queries were first passed through GPT4ALL’s Meta Llama 3 8B Instruct LLM model to expand the query with more synonyms and context. 

#### 3.3.3 Accuracy Score Calculations

Once the raw scores were all generated, each score were mapped from 0 to 1 so the minimum distance is equal to 0 and the maximum distance was equal to 1 using the following equation:

$$
s_i = 1 - \frac{d_i - d_{min}}{d_{max} - d_{min}}
$$
where $s_i$ represents the score for item $i$ and $d_i$ represents the distance from the query vector for each item $i$. The variables $d_{min}$ and $d_{max}$ represents the minimum distance and maximum distance. This newly scaled score was then pass through a sigmoid function:

$$
\sigma(i)​=\frac{1}{1+e^{-α(s_i​−0.5)}}​
$$
where $\alpha$ represents the steepness and  $s_i​−0.5$ forces the middle similarity to map to 0.5. This was done to exaggerate higher and lower scores to reduce noise, so similar matches get better separated from dissimilar matches. For this function $\alpha = 10$ was used to determine these scores. Finally, the score was then multiplied by 100:

$$
\text{Accuracy}_i​=100\times \sigma(i)​
$$
to make the result easier to interpret for users as 0-100 scales are more familiar among users. This is the accuracy score that is used to sort the transcripts in order of descending score. Users are then also given the option to export the resulting accuracy scores to a CSV for further analysis. An example of illustrating the scored results using the query "factory" can be seen in figure 3.

![[Screenshot 2025-12-13 at 3.19.06 AM.webp]]


## 4. Evaluation 

### 4.1 Geo-Synchronized Audio ReAnnotation Performance

Performance of Geo-Synchronized Audio ReAnnotation was performed by comparing the speed required to add new annotation data and creating a map of the data points and the location accuracy against two differing conventional methods. The first conventional method is through file manipulation of the narrative data files and GPS files, and the second method is by manually placing points directly on the map and adding annotation on top. ArcGIS Pro was used to map the added data through the conventional methods while Geo-Synchronized Audio ReAnnotation utilized the map built into the interface. Test subjects were given 3 different prompts to record and transcribe along with corresponding timestamp data from the video to add onto the Newburgh Heights Air Quality SVG. This was done to simulate what data the user would know when deciding to add their annotation while watching the spatial video. The test subject used for this evaluation was me. Table 1 shows all three transcripts and timestamps used for the test

Table 1: Timestamp and Transcript data used to assess the three annotation methods: Geo-Synchronized Audio ReAnnotation, file manipulation, direct point placing. The timestamps were chosen randomly while the transcripts were made to simulate some possible commentary.

| Timestamp | Transcript                                                      |
| --------- | --------------------------------------------------------------- |
| 00:20:54  | I see a mound of smoke coming from that factory                 |
| 00:40:16  | The cars here are always covered in black dust                  |
| 01:02:21  | There is a lot of truck traffic around these parts of the area. |
### 4.2 Semantic Search Performance

Performance of Semantic Search was compared to keyword search in returning points for three user defined queries regarding various features present, and comparing these point to the verified location of these features. Performance was determined by the number of data point by how many verified locations did each search successfully retrieve. Due to the nature of how commentary may contain desired terms even if off-location, points that exist where verified data points are not present are not considered for this evaluation. These verified locations were determined by manually analysis of the transcript as well as through visual observations. Thus, it is unfair to expect both search functions to cross reference with visual observation data to filter out results where the physical feature does not exist. These user queries were limited to single words due to keyword search reliance on exact matches, making longer queries unlikely to produce any results. The query "Factory" was used due to factory locations being the easiest from the dataset to verify. A threshold of 95 was used on the accuracy score to filter out non-matches and any noise.


## 5. Results

### 5.1 Geo-Synchronized Audio ReAnnotation Performance

After running through all three methods, the time it took for Geo-Synchronized Audio ReAnnotation, file manipulation, and direct point plotting was 0.4770, 3.9787, and 1.9958 minutes respectively. See Table 2 for the exact data for each method and transcript.


Table 2: The table below shows how long it took for each method to add new annotation and to map the data. The times are measured in minutes.

| Timestamp | Transcript                                                     | My Interface (min) | File Manipulation(min) | Direct Plotting (min) |
| --------- | -------------------------------------------------------------- | ------------------ | ---------------------- | --------------------- |
| 00:20:54  | I see a mound of smoke coming from that factory                | 0.5848             | 5.6993                 | 2.1495                |
| 00:40:16  | The cars here are always covered in black dust                 | 0.4023             | 3.0127                 | 2.2852                |
| 01:02:21  | There is a lot of truck traffic around these parts of the area | 0.4438             | 3.2238                 | 1.5530                |

For Geo-Synchronized Audio ReAnnotation and file manipulation methods, the GPS coordinates are exact as they were derived from linking the video timestamp to the GPS data. Direct plotting did not have exact GPS coordinates, causing these points to be offset from the exact point by an average of 679 meters. Table 3 shows the exact coordinates for the exact GPS coordinates as well, the coordinates from direct plotting, and the distances for each transcript. 



Table 3: Table 3 shows the exact coordinates for each transcript derived from linking timestamp data to the GPS data. The coordinates from direct plotting and error distances between direct plotting and the exact distances are also shown. Transcript 1, 2, and 3 refers to "I see a mound of smoke coming from that factory", "The cars here are always covered in black dust", and "There is a lot of truck traffic around these parts of the area" respectively.

| Transcript | Exact Latitude | Exact Longitude | Direct Plotting | Direct Plotting | Error Distance (m) |
| ---------- | -------------- | --------------- | --------------- | --------------- | ------------------ |
| 1          | -81.659081     | 41.44568        | -81.669063      | 41.447036       | 846                |
| 2          | -81.664064     | 41.44782        | -81.669026      | 41.453677       | 771                |
| 3          | -81.664158     | 41.45028        | -81.669026      | 41.449291       | 420                |


### 5.2 Semantic Search Results

In total, there were 8 different verified locations of factories that was present in the transcript. Semantic Search was able to retrieve 6 of these locations while keyword search was only managed to retrieve two of these locations. The results of comparing keyword and semantic search visualized and mapped can be seen in Figure 4. Both maps were created using ArcGIS Pro.

![[Screenshot 2025-12-13 at 3.22.22 AM.webp]]


## 6. Discussion

### 6.1 Geo-Synchronized Audio ReAnnotation Performance


For all three transcripts, Geo-Synchronized Audio ReAnnotation outperformed file manipulation and direct plotting in speed. Geo-Synchronized Audio ReAnnotation would take around half a minute while the other methods take anywhere from 1.5-5.5 minutes, thus demonstrating that Geo-Synchronized Audio ReAnnotation reduces the amount of time for users to annotate pre-existing SVGs. The main reason for the time save is that the interface handles all the syncing in the background automatically while file manipulation requires typing all the data and making sure the time formats between the GPS data and narrative data match. Direct Plotting also required for users to fill out every attribute for each point created. Geo-Synchronized Audio ReAnnotation automatically creates and fills out these attributes, preventing the need to manual label data points. Thus, the automation of data post processing made Geo-Synchronized Audio ReAnnotation faster than the other two methods.

Geo-Synchronized Audio ReAnnotation and file manipulation both had exact coordinates for all three transcripts due to the nature of their workflow syncing timestamp data with GPS data. Direct plotting's workflow does not feature this, resulting in points being placed in the approximately vicinity, resulting in the loss of accuracy. Thus, while direct point plotting proved faster on average compared to file manipulation, it comes at a cost of location accuracy. Geo-Synchronized Audio ReAnnotation is able to provide the benefit of being faster while still maintaining accuracy, and thus, proving to be the better workflow compared to conventional methods. This also means that Geo-Synchronized Audio ReAnnotation enhances scalability of SVG datasets.

Future improvements on Geo-Synchronized Audio ReAnnotation could include a central database and version control to allow multiple experts and research teams to collaborate on one SVG simultaneously rather than iteratively. Currently, this prototype produces a new empty database for each expert researches send the prototype out to. Thus data still remains fragmented among the different perspectives and some file manipulation may be required to join these perspectives together to have on all encompassing dataset featuring all the add annotations. Versioning would resolve this issue by having users to push and pull to and from a central database, allowing all users to contribute as well as have all access to the latest updated information. 

### 6.2 Semantic Search

Semantic search was able to outperform keyword search in feature retrieval, demonstrating the usefulness and power of semantic search. There was also some points that semantic search retrieved that did not match the verified locations. This can be attributed to some point in the transcript where factories or synonyms of factories getting mentioned in a more general context rather indicating the physical presence of one. Thus, this spatial fuzziness is one limitation that semantic search result is unable to overcome as it can not take into account any visual observation data. Additionally, the models used to implement semantic search are not very powerful due to a limit on available processing power. These two factors help contribute to some points getting retrieved even though they do not reflect the true physical world. Nevertheless, semantic search still remains a powerful way to analyze transcripts, allowing researchers to handle larger datasets accurately and uncover implicit meanings/patterns. Future improvements can be made by utilizing more powerful models as well as implementing image search for cross checking with semantic search to reduce spatial fuzziness within data.


## 8. Acknowledgements

I would like to thank GIS Health & Hazards Lab (GHHL) as well as Dr. Curtis and Jay for providing guidance and assistance.


## 9. Data Availability

Video data can be acquired by contacting the GIS Health & Hazards Lab (GHHL) for their Newburgh Heights Air Quality dash cam data. GPS data and narrative data can be found along with the code in the Github repository


## 10. Code Availability

Code used to build and implement this interface can be found here: https://github.com/ZhaoDylan099/GIS_Video_Geotagging
The code to build the interface is labeled as app.py and the code used to build the database tables are found in database.sql.



## 11. References

1. Ajayakumar, J., Curtis, A., Smith, S., & Curtis, J. W. (2019). The use of geonarratives to add context to fine-scale geospatial research. _International Journal of Environmental Research and Public Health, 16_(3), 515. [https://doi.org/10.3390/ijerph16030515](https://doi.org/10.3390/ijerph16030515)

2. Badland, H. M., et al. (2010). Can virtual streetscape audits reliably replace physical streetscape audits? _Journal of Urban Health_. [https://pubmed.ncbi.nlm.nih.gov/21104331/](https://pubmed.ncbi.nlm.nih.gov/21104331/)

3. Curtis, A., Blackburn, J. K., Widmer, J. M., Morris, J. G., & others. (2013). A ubiquitous method for street-scale spatial data collection and analysis in challenging urban environments: Mapping health risks using spatial video in Haiti. _International Journal of Health Geographics, 12_, 21. [https://doi.org/10.1186/1476-072X-12-21](https://doi.org/10.1186/1476-072X-12-21)

4. Curtis, A., Curtis, J. W., Shook, E., Smith, S., Jefferis, E., & Porter, L. (2015). Spatial video geonarratives and health: Case studies in post-disaster recovery, crime, mosquito control, and tuberculosis in the homeless. _International Journal of Health Geographics, 14_, 22. [https://doi.org/10.1186/s12942-015-0014-8](https://doi.org/10.1186/s12942-015-0014-8)
5. Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. _Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT 2019), Volume 1 (Long and Short Papers)_, 4171–4186. [https://doi.org/10.18653/v1/N19-1423](https://doi.org/10.18653/v1/N19-1423)

6. Mai, G., Janowicz, K., Prasad, S., Shi, M., Cai, L., Zhu, R., Regalia, B., & Lao, N. (2020). Semantically-enriched search engine for geoportals: A case study with ArcGIS Online. _AGILE GIScience Series, 1_, Article 13. [https://doi.org/10.5194/agile-giss-1-13-2020](https://doi.org/10.5194/agile-giss-1-13-2020)

7. Queralt, A., et al. (2021). Reliability of streetscape audits comparing on-street and online observations. _International Journal of Health Geographics, 20_, Article 27. https://doi.org/10.1186/s12942-021-00261-5
8. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. _Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)_, 3982–3992. https://doi.org/10.18653/v1/D19-1410

9. Ristea, A., Leitner, M., Resch, B., & Stratmann, J. (2021). Applying spatial video geonarratives and physiological measurements to explore perceived safety in Baton Rouge, Louisiana. _International Journal of Environmental Research and Public Health, 18_(3), 1284. https://doi.org/10.3390/ijerph18031284

10. Weckmüller, D., Dunkel, A., & Burghardt, D. (2025). Embedding-based multilingual semantic search for geo-textual data in urban studies. _Journal of Geovisualization and Spatial Analysis, 9_, 31. [https://doi.org/10.1007/s41651-025-00232-5](https://doi.org/10.1007/s41651-025-00232-5)

11. Zhang, F., et al. (2018). Measuring human perceptions of a large-scale urban region using machine learning. _Landscape and Urban Planning, 180_, 148–160. [https://hdl.handle.net/1783.1/120207](https://hdl.handle.net/1783.1/120207)