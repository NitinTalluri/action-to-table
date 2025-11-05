import AddIcon from "@mui/icons-material/Add";
import CancelIcon from "@mui/icons-material/Cancel";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import SaveIcon from "@mui/icons-material/Save";
import { IconButton, styled, TextField } from "@mui/material";
import { useState } from "react";

import { TTag } from "~/domain/Tags";
import invariant from "~/utils/invariant";

import { useCreateTag } from "./useCreateTag";
import { useDeleteTag } from "./useDeleteTag";
import { useUpdateTag } from "./useUpdateTag";

const TagStyled = styled("div")({
  display: "inline-flex",
  alignItems: "center",
  margin: "5px",
  borderRadius: "15px",
  border: "1px solid #ccc",
  background: "white",
  minWidth: "50px",
});

const EditFormStyled = styled("div")({
  display: "flex",
  flexDirection: "column",
  padding: "10px",
});

const TagNameStyled = styled("div")({
  padding: "6px",
});

const ButtonGroupStyled = styled("div")({
  marginLeft: "6px",
});

const TagListStyled = styled("div")({
  display: "flex",
  alignItems: "center",
  flexWrap: "wrap",
});

const NewTagStyled = styled("div")({
  cursor: "pointer",
  display: "inline-flex",
  alignItems: "center",
  margin: "5px",
  borderRadius: "15px",
  border: "1px solid #ccc",
  background: "white",
});

const CreateFormStyled = styled("div")({
  display: "inline-flex",
  alignItems: "center",
  margin: "5px",
  padding: "10px",
  border: "1px solid #ccc",
  borderRadius: "15px",
  background: "white",
});

const AddIconStyled = styled("div")({
  marginRight: "8px",
});

const EditForm = ({
  name,
  desc,
  setName,
  setDesc,
}: {
  name: string;
  desc: string;
  setName: (n: string) => void;
  setDesc: (d: string) => void;
}) => {
  return (
    <EditFormStyled>
      <TextField
        variant="filled"
        sx={{ paddingBottom: "10px" }}
        label={"Tag Name"}
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <TextField
        variant="filled"
        style={{ padding: 0 }}
        label={"Tag Description"}
        value={desc}
        onChange={(e) => setDesc(e.target.value)}
      />
    </EditFormStyled>
  );
};
const Tag = ({
  tag,
  editingTagsetId,
  selectedEngagementId,
}: {
  tag: TTag;
  editingTagsetId: number | null;
  selectedEngagementId: number | null;
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(tag.tag_name);
  const [desc, setDesc] = useState(tag.tag_desc || "");

  const onUpdateTag = useUpdateTag(selectedEngagementId);
  const handleSave = async () => {
    const updatedTag = { ...tag, tag_name: name, tag_desc: desc };
    onUpdateTag(updatedTag);
    setIsEditing(false);
  };

  const onDeleteTag = useDeleteTag(selectedEngagementId);
  const handleDelete = () => {
    onDeleteTag(tag.tag_id);
  };

  return (
    <TagStyled>
      {isEditing ? (
        <EditForm name={name} desc={desc} setName={setName} setDesc={setDesc} />
      ) : (
        <TagNameStyled>{name}</TagNameStyled>
      )}
      {editingTagsetId && (
        <ButtonGroupStyled>
          <IconButton
            size="small"
            onClick={isEditing ? handleSave : () => setIsEditing(true)}
          >
            {isEditing ? <SaveIcon /> : <EditIcon />}
          </IconButton>
          <IconButton
            size="small"
            onClick={isEditing ? () => setIsEditing(false) : handleDelete}
          >
            {isEditing ? <CancelIcon /> : <DeleteIcon />}
          </IconButton>
        </ButtonGroupStyled>
      )}
    </TagStyled>
  );
};

const TagList = ({
  initialTags,
  selectedEngagementId,
  editingTagsetId,
  selectedTagsetId,
}: {
  initialTags: TTag[];
  selectedEngagementId: number | null;
  editingTagsetId: number | null;
  selectedTagsetId: number | null;
}) => {
  const [isCreating, setIsCreating] = useState(false);
  const [newTagName, setNewTagName] = useState("");
  const [newTagDesc, setNewTagDesc] = useState("");

  const { onCreateTag } = useCreateTag(selectedEngagementId);
  const handleCreateSave = () => {
    invariant(selectedTagsetId, "Tagset ID is required to create a tag");
    onCreateTag(
      {
        tag_name: newTagName,
        tag_desc: newTagDesc,
        tagset_id: selectedTagsetId,
      },
      () => {
        setIsCreating(false);
        setNewTagName("");
        setNewTagDesc("");
      },
    );
  };

  return (
    <TagListStyled>
      {initialTags.map((tag) => (
        <Tag
          key={tag.tag_id}
          selectedEngagementId={selectedEngagementId}
          tag={tag}
          editingTagsetId={editingTagsetId}
        />
      ))}
      {editingTagsetId && !isCreating && (
        <NewTagStyled onClick={() => setIsCreating(true)}>
          <TagNameStyled>Create new Tag</TagNameStyled>
          <AddIconStyled>
            <AddIcon />
          </AddIconStyled>
        </NewTagStyled>
      )}
      {isCreating && (
        <CreateFormStyled>
          <EditForm
            name={newTagName}
            desc={newTagDesc}
            setName={setNewTagName}
            setDesc={setNewTagDesc}
          />
          <ButtonGroupStyled>
            <IconButton size="small" onClick={handleCreateSave}>
              <SaveIcon />
            </IconButton>
            <IconButton size="small" onClick={() => setIsCreating(false)}>
              <CancelIcon />
            </IconButton>
          </ButtonGroupStyled>
        </CreateFormStyled>
      )}
    </TagListStyled>
  );
};

export default TagList;
