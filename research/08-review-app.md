# Review: annotation storage, media, deep links, from Autodesk's own documentation

Research pass, 2026-09-15. Official help pages were read through Autodesk's redirect service to
their `cloudhelp` mirrors, since the `help.autodesk.com/view/SGSUB/ENU/?guid=` shells 404 to a
fetcher. [official] = help.autodesk.com or developers.shotgridsoftware.com; [announce] = Autodesk
blog or staff post; [community] = forum, unconfirmed; [inference] = the agent's.

## 1. Annotation storage

**Legacy tools (Overlay Player, Screening Room, RV, the iPhone app): a burned-in frame image attached
to the Note.** "that frame, and any other frame you marked up, is automatically attached to your note
and displayed via a thumbnail" ([official, Overlay Player](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-review-approval/SG_Supervisor_Artist_sa_review_approval_sa_overlay_player_html.html)).
The iPhone doc: "Press 'Done' to attach the annotation as a frame to your note"
([official](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-mobile-review/SG_Supervisor_Artist_sa_review_iphone_using_html.html)).

**The filename convention is official.** The Thumbnail Configuration page: "If you have a Note 1 that
receives its thumbnail from an annotated frame on a Version, then the Image Source entity for Note 1
would be `annot_version_6005.0.png` (this is the attachment entity)", and "The Image Source entity
can be retrieved via the API, though it cannot be set via the API"
([official, SG-Administrator](https://help.autodesk.com/cloudhelp/ENU/SG-Administrator/files/ar-site-configuration/SG_Administrator_ar_site_configuration_ar_thumbnail_configuration_html.html)).
No official page describes a transparent overlay or vector data. [inference] A flat composited frame.

**The new Review app (GA June 2026): storage undocumented.** The Review pages describe drawing, shapes,
text, pen pressure and "View Annotations in Player" but name no entity, field, filename or schema
([official, SA_Review_Main](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/SA_Review_Main.html)).
What's New 8.86 says only "Draw annotations on frames and add notes that stay connected to your
production data". A user reports "Review only allows to view annotations that were created in Review"
([community t/20899, Aug 2026](https://community.shotgridsoftware.com/t/how-to-show-annotations-in-rv/20899)).
[inference] Review keeps its own per-frame record, not the legacy attachments.

## 2. Media fields and playback in a browser

[official] Upload to `sg_uploaded_movie`; transcoding produces "streamable 1080p, H.264" media and
thumbnails; until then the Version shows "No Playable Media"
([Transcoding](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-review-approval/SG_Supervisor_Artist_sa_review_approval_sa_transcoding_html.html)).
[official] DIY transcoding names `sg_uploaded_movie_mp4`, `sg_uploaded_movie_frame_rate` ("defaults to
24", set it for anything else) and a hidden `sg_uploaded_movie_image`; uploading an `.mp4` to the mp4
field bypasses server transcoding; "Some browsers may not properly detect the movie format without
these specific extensions" ([DIY transcoding](https://help.autodesk.com/cloudhelp/ENU/SG-Administrator/files/ar-site-configuration/SG_Administrator_ar_site_configuration_ar_diy_transcoding_html.html)).
`sg_uploaded_movie_webm` is only in an old knowledge-base snippet; beta feedback reported WebM hanging
in Creative Review (t/20100). Weakly sourced.

URLs: an attachment value is a `this_file` dict with `url`, `name`, `content_type`, `link_type`
([python-api attachments cookbook](https://developers.shotgridsoftware.com/python-api/cookbook/attachments.html));
Autodesk "generates S3 Links to your sources and transcoded media", transferred "directly to/from AWS
S3" ([Media Isolation](https://developers.shotgridsoftware.com/a3c0e676/)). No official page states
the expiry; the corpus measured `X-Amz-Expires=900` (`field_types/image`, `recipes/013`).

Not officially documented anywhere found: `sg_uploaded_movie_transcoding_status`, `sg_first_frame`,
`sg_last_frame`, `frame_count`, the frame-to-time mapping, CORS on the S3 URLs. [inference]
`time = (frame - sg_first_frame) / sg_uploaded_movie_frame_rate`. The corpus's finding 022 measured
the status field flipping and the mp4 field describing the old file after a replacement.

## 3. Deep links into Review and RV

- `https://<site>/page/media_center` is the only fully documented page URL; the Media App also
  offers right-click → "Copy Internal Version Link"
  ([official](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-review-approval/SG_Supervisor_Artist_sa_review_approval_sa_media_app_playlists_html.html)).
- `/page/screening_room?entity_type=Version&entity_id=N` and `media_center?project_id=…&entity_type=
  Version&entity_id=N`: community only. No `frame=` parameter is documented anywhere.
- Review: no URL format documented. Entry is right-click → "Play in Review", or a playable thumbnail
  when an admin set Review as the default player ([SA_Review_Open](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-creative-review/SA_Review_Open.html)).
  Live Review has a copyable session link; format unpublished.
- RV: `rvlink://<RV commandline>`, e.g. `rvlink:// -l -play /path/to/movie.mov`, or the baked hex form
  from `-bakeURL`; Autodesk's manual now redirects to
  [ASWF Open RV, chapter C](https://aswf-openrv.readthedocs.io/en/latest/rv-manuals/rv-user-manual/rv-user-manual-chapter-c.html).
  No frame or Version-id parameter. Attachments with `link_type: web` may hold `rvlink://` URLs.

## 4. Notes and frames

No frame field on Note is documented. The frame travels in the annotation attachment's filename,
which is why it renders on the note thumbnail. Review's notes panel shows replies only since
v0.227.9 (27 Aug 2026), and "Creating replies and editing/deleting both replies and notes will be
coming in a future release" ([announce, t/20913](https://community.shotgridsoftware.com/t/creative-review-public-beta-v0-227-9-released/20913)).
Replies carrying annotations: not supported; a feature request exists.

## 5. What third parties may do; deprecations

No embed, iframe or player SDK for Review is documented: absence, not prohibition. The REST API
documents uploads in detail and no attachment download route was found; the Python API's
`download_attachment` / `get_attachment_download_url` are the documented path (the corpus measured
the field's presigned `url` as the REST equivalent, `recipes/013`). No deprecation dates: Review
"consolidates the best features of existing media review tools like Create, Screening Room, and the
Review Notes app" and can replace the Overlay Player as default player; staff wrote "a consolidation
effort is on the way" ([t/20851](https://community.shotgridsoftware.com/t/introducing-review-in-flow-production-tracking/20851)).
GA June 2026 (8.86); shapes and text July 2026 (8.87); RV 2025.1 can join Review sessions.

## What a third-party notes page can honestly offer

**Show the annotated frame.** Yes, reliably, for legacy annotations: the Note's Attachments, one PNG
per frame, the frame number in the filename, officially exemplified. Annotations drawn in the new
Review app may not exist as such attachments; nothing documents where they live.

**Play media with frame markers.** Yes: `<video>` on `sg_uploaded_movie_mp4`, falling back to
`sg_uploaded_movie`, URLs fetched just in time and never stored. Markers need
`sg_uploaded_movie_frame_rate` (read it, never assume 24) and `sg_first_frame`, which is not
officially documented, so frame-to-time is best effort. Browser seeking is not frame-accurate; the
marker shows the burned-in frame image.

**Hand off to Review.** One documented deep link, the Media App page; no Review URL, no `frame=`,
no embed. Link to the Version, and the person right-clicks "Play in Review". `rvlink://` is a real,
documented "open in RV" for those who have it, with no frame parameter.

## Sources

Fetched: SG-Supervisor-Artist review workflow, overlay player, screening room, notes, transcoding,
transcoding services, media app and playlists, iPhone review, SA_Review_Main, SA_Review_Open,
SA_Review_Administration, SA_Review_Live_Review; SG-Administrator thumbnail configuration, DIY
transcoding; SG-Producer review notes, client review; SG-Whats-New 8.86 and shapes/text; python-api
attachments cookbook and reference v3.10.3; REST API landing; Media Isolation; tk-framework-qtwidgets
note_input_widget; Autodesk blog 2026-06-29; community 20851, 20870, 20913, 20695, 20100, 20899,
9907, 7212, 9363, 18710. Failed: knowledge.autodesk.com mirrors (503), four Autodesk KB articles
(403), the SGSUB guid shells (404), several guessed Review page paths (404).
