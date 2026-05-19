let people = JSON.parse(localStorage.getItem('people')) || [];
let nextId = JSON.parse(localStorage.getItem('nextId')) || 1;
let selectedPersonIndex = null;

const treeContainer = document.getElementById('treeContainer');
const addPersonBtn = document.getElementById('addPersonBtn');
const infoPanel = document.getElementById('infoPanel');
const personName = document.getElementById('personName');
const personBirthplace = document.getElementById('personBirthplace');
const personStories = document.getElementById('personStories');
const savePersonBtn = document.getElementById('savePersonBtn');
const closePanelBtn = document.getElementById('closePanelBtn');
const relationTargetId = document.getElementById('relationTargetId');
const relationType = document.getElementById('relationType');
const addRelationBtn = document.getElementById('addRelationBtn');
const deleteRelationBtn = document.getElementById('deleteRelationBtn');

function renderTree() {
  treeContainer.innerHTML = '';
  people.forEach((person, index) => {
    const div = document.createElement('div');
    div.className = 'personBox';
    div.textContent = `#${person.id} ${person.name || 'Unnamed'}`;
    div.addEventListener('click', () => openInfoPanel(index));
    treeContainer.appendChild(div);
  });
}

function openInfoPanel(index) {
  selectedPersonIndex = index;
  const person = people[index];
  personName.value = person.name || '';
  personBirthplace.value = person.birthplace || '';
  personStories.value = person.stories || '';
  infoPanel.classList.remove('hidden');
}

function closeInfoPanel() {
  infoPanel.classList.add('hidden');
}

function savePerson() {
  const person = people[selectedPersonIndex];
  person.name = personName.value;
  person.birthplace = personBirthplace.value;
  person.stories = personStories.value;
  localStorage.setItem('people', JSON.stringify(people));
  renderTree();
  closeInfoPanel();
}

addPersonBtn.addEventListener('click', () => {
  const newPerson = { 
    id: nextId,            // assign current number
    name: '', 
    birthplace: '', 
    stories: '', 
    relationships: [] 
  };
  people.push(newPerson);
  nextId++;
  localStorage.setItem('people', JSON.stringify(people));
  localStorage.setItem('nextId', nextId);
  renderTree();
});
const clearTreeBtn = document.getElementById('clearTreeBtn');

clearTreeBtn.addEventListener('click', () => {
  if (confirm("Are you sure you want to clear the tree? This will delete all saved people.")) {
    people = [];
    nextId = 1;
    localStorage.removeItem('people');
    localStorage.removeItem('nextId'); // wipe from storage
    renderTree(); // refresh the display
  }
});

addRelationBtn.addEventListener('click', () => {
  const targetId = parseInt(relationTargetId.value);
  if (!targetId || !relationType.value) return alert("Enter valid ID and relationship type");

  const person = people[selectedPersonIndex];
  person.relationships.push({ type: relationType.value, targetId: targetId });

  localStorage.setItem('people', JSON.stringify(people));
  alert(`Linked #${person.id} as ${relationType.value} of #${targetId}`);
});

deleteRelationBtn.addEventListener('click', () => {
  const targetId = parseInt(relationTargetId.value);
  if (!targetId || !relationType.value) return alert("Enter valid ID and relationship type to delete");

  const person = people[selectedPersonIndex];

  // Filter out (remove) matching relationship
  person.relationships = person.relationships.filter(rel => {
    return !(rel.type === relationType.value && rel.targetId === targetId);
  });

  localStorage.setItem('people', JSON.stringify(people));
  alert(`Deleted ${relationType.value} link to #${targetId} from #${person.id}`);
});

savePersonBtn.addEventListener('click', savePerson);
closePanelBtn.addEventListener('click', closeInfoPanel);

renderTree();
